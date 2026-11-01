#!/usr/bin/env python3
"""LoRA supervised fine-tuning on the DGX Spark (GB10, 128 GB unified memory) with Unsloth, TRL fallback.

  python scripts/05_finetune_unsloth.py --base Qwen/Qwen3-8B --train data/sft/mix_train.jsonl --dev data/sft/dev.jsonl \
      --out runs/qwen3-8b-atc --epochs 2
  python scripts/05_finetune_unsloth.py --base nvidia/Llama-3.1-Nemotron-Nano-8B-v1 --out runs/nemotron-nano-8b-atc ...
  python scripts/05_finetune_unsloth.py --base /mnt/hackssd/GB10_ARSENAL/models/<Qwen3-4B-Instruct-2507 dir> --out runs/qwen3-4b-atc ...
  smoke test:  --max-steps 20

Outputs under --out:
  adapter/        LoRA adapter (upload this to Fireworks for the same base, or load with vLLM --enable-lora)
  merged/         merged bf16 weights (serve directly with vLLM)
  train_log.json  loss curve + eval loss + config (cite in README)

Spark notes: NVIDIA's playbook covers Unsloth on DGX Spark (build.nvidia.com/spark/unsloth). If `import unsloth`
fails, the TRL+PEFT path below runs on plain transformers inside the nvcr.io/nvidia/pytorch container.
"""
import argparse, json, os, time


def build_text(tok, messages):
    try:
        return tok.apply_chat_template(messages, tokenize=False, enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(messages, tokenize=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen3-8B")
    ap.add_argument("--train", default="data/sft/mix_train.jsonl")
    ap.add_argument("--dev", default="data/sft/dev.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--max-seq", type=int, default=1024)
    ap.add_argument("--bsz", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--no-merge", action="store_true")
    ap.add_argument("--force-trl", action="store_true", help="skip Unsloth even if importable")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    from datasets import load_dataset
    ds = load_dataset("json", data_files={"train": args.train, "dev": args.dev})

    use_unsloth = False
    if not args.force_trl:
        try:
            from unsloth import FastLanguageModel
            use_unsloth = True
        except Exception as e:
            print(f"[warn] unsloth unavailable ({e!r}); using TRL + PEFT")

    if use_unsloth:
        model, tok = FastLanguageModel.from_pretrained(args.base, max_seq_length=args.max_seq, load_in_4bit=False, dtype=None)
        model = FastLanguageModel.get_peft_model(
            model, r=args.r, lora_alpha=args.alpha, lora_dropout=0.0, bias="none",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            use_gradient_checkpointing="unsloth", random_state=42)
    else:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig, get_peft_model
        tok = AutoTokenizer.from_pretrained(args.base)
        model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16, device_map="auto")
        model.gradient_checkpointing_enable()
        model = get_peft_model(model, LoraConfig(r=args.r, lora_alpha=args.alpha, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                                                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def fmt(ex):
        return {"text": build_text(tok, ex["messages"])}
    train = ds["train"].map(fmt, remove_columns=[c for c in ds["train"].column_names if c != "text"])
    dev = ds["dev"].map(fmt, remove_columns=[c for c in ds["dev"].column_names if c != "text"])

    import inspect
    from trl import SFTTrainer, SFTConfig
    # TRL >= 1.x dropped warmup_ratio (warmup_steps < 1 is a ratio) and renamed tokenizer= to processing_class=
    warmup = {"warmup_ratio": 0.05} if "warmup_ratio" in inspect.signature(SFTConfig.__init__).parameters else {"warmup_steps": 0.05}
    cfg = SFTConfig(
        output_dir=os.path.join(args.out, "ckpt"), per_device_train_batch_size=args.bsz, gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs, max_steps=args.max_steps, learning_rate=args.lr, lr_scheduler_type="cosine", **warmup,
        logging_steps=10, eval_strategy="steps", eval_steps=50, save_strategy="no", bf16=True, fp16=False,
        max_length=args.max_seq, dataset_text_field="text", packing=False, report_to="none", seed=42,
    )
    tok_kw = "processing_class" if "processing_class" in inspect.signature(SFTTrainer.__init__).parameters else "tokenizer"
    trainer = SFTTrainer(model=model, train_dataset=train, eval_dataset=dev, args=cfg, **{tok_kw: tok})
    # loss only on the assistant turn (the JSON), not on the prompt
    try:
        from unsloth.chat_templates import train_on_responses_only
        if use_unsloth:
            a = "<|im_start|>assistant\n" if "<|im_start|>" in build_text(tok, [{"role": "user", "content": "x"}]) else "<|start_header_id|>assistant<|end_header_id|>\n\n"
            u = "<|im_start|>user\n" if a.startswith("<|im_start|>") else "<|start_header_id|>user<|end_header_id|>\n\n"
            trainer = train_on_responses_only(trainer, instruction_part=u, response_part=a)
    except Exception as e:
        print(f"[warn] train_on_responses_only not applied: {e!r} (loss includes prompt tokens)")

    t0 = time.time()
    out = trainer.train()
    ev = trainer.evaluate()
    log = {"base": args.base, "config": vars(args), "train_runtime_s": time.time() - t0, "train_loss": out.training_loss,
           "eval": ev, "log_history": trainer.state.log_history}
    json.dump(log, open(os.path.join(args.out, "train_log.json"), "w"), indent=2)
    model.save_pretrained(os.path.join(args.out, "adapter")); tok.save_pretrained(os.path.join(args.out, "adapter"))
    if not args.no_merge:
        if use_unsloth:
            model.save_pretrained_merged(os.path.join(args.out, "merged"), tok, save_method="merged_16bit")
        else:
            merged = model.merge_and_unload(); merged.save_pretrained(os.path.join(args.out, "merged")); tok.save_pretrained(os.path.join(args.out, "merged"))
    print(f"done in {time.time() - t0:.0f}s; train_loss={out.training_loss:.4f} eval={ev}")


if __name__ == "__main__":
    main()
