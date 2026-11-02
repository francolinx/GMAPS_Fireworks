#!/usr/bin/env python3
"""Fireworks route, end to end, from any machine with the Python SDK (no firectl needed).

  export FIREWORKS_API_KEY=...   # never commit it
  python3 scripts/15_fireworks_sft.py upload  data/sft/mix_train_v2.jsonl atc-mix-v2
  python3 scripts/15_fireworks_sft.py upload  data/sft/dev.jsonl          atc-dev
  python3 scripts/15_fireworks_sft.py train   atc-mix-v2 --eval atc-dev --base accounts/fireworks/models/qwen3-8b \
                                              --epochs 3 --lr 1e-4 --rank 16 --out atc-qwen3-8b-v2
  python3 scripts/15_fireworks_sft.py status  <job-id>          # polls until done, prints the output model name
  python3 scripts/15_fireworks_sft.py models                    # list your models (find the trained LoRA)
  python3 scripts/15_fireworks_sft.py deploy  <output-model>    # serverless LoRA deployment if the base supports it

Record the job id, the output model name and the deployed model name in README §7 and results/prices.json.
"""
import argparse, json, os, sys, time

from fireworks import Fireworks


def client():
    key = os.environ.get("FIREWORKS_API_KEY")
    if not key:
        sys.exit("set FIREWORKS_API_KEY")
    return Fireworks(api_key=key)


def account_id(c):
    aid = os.environ.get("FIREWORKS_ACCOUNT_ID")
    if aid:
        return aid
    try:
        accts = c.accounts.list()
        items = getattr(accts, "accounts", None) or []
        if items:
            name = items[0].name  # "accounts/<id>"
            return name.split("/")[-1]
    except Exception as e:
        print(f"[warn] could not list accounts: {e!r}; set FIREWORKS_ACCOUNT_ID")
    sys.exit("set FIREWORKS_ACCOUNT_ID (from the Fireworks dashboard URL)")


def cmd_upload(args):
    c = client(); aid = account_id(c)
    n = sum(1 for l in open(args.file, encoding="utf-8") if l.strip())
    print(f"creating dataset {args.dataset_id} in account {aid} ({n} examples) ...")
    c.datasets.create(account_id=aid, dataset_id=args.dataset_id, dataset={"display_name": args.dataset_id, "example_count": n})
    with open(args.file, "rb") as fh:
        c.datasets.upload(dataset_id=args.dataset_id, account_id=aid, file=fh)
    for _ in range(60):
        d = c.datasets.get(dataset_id=args.dataset_id, account_id=aid)
        state = getattr(d, "state", None)
        print("  state:", state)
        if str(state).upper().endswith("READY"):
            break
        time.sleep(5)
    print(f"dataset: accounts/{aid}/datasets/{args.dataset_id}")


def cmd_train(args):
    c = client(); aid = account_id(c)
    kwargs = dict(
        account_id=aid,
        dataset=f"accounts/{aid}/datasets/{args.dataset}",
        base_model=args.base,
        epochs=args.epochs, learning_rate=args.lr, lora_rank=args.rank,
        output_model=args.out, display_name=args.out, is_turbo=not args.no_turbo,
    )
    if args.eval:
        kwargs["evaluation_dataset"] = f"accounts/{aid}/datasets/{args.eval}"
    if args.max_ctx:
        kwargs["max_context_length"] = args.max_ctx
    job = c.supervised_fine_tuning_jobs.create(**kwargs)
    jid = job.name.split("/")[-1] if hasattr(job, "name") else job
    print("job:", job.name if hasattr(job, "name") else job)
    print(json.dumps({k: str(v) for k, v in kwargs.items() if k != "account_id"}, indent=2))
    print(f"\npoll with: python3 scripts/15_fireworks_sft.py status {jid}")


def cmd_status(args):
    c = client(); aid = account_id(c)
    while True:
        j = c.supervised_fine_tuning_jobs.get(supervised_fine_tuning_job_id=args.job_id, account_id=aid)
        state = str(getattr(j, "state", ""))
        print(time.strftime("%H:%M:%S"), state, getattr(j, "status", "") or "")
        if any(s in state.upper() for s in ("COMPLETED", "FAILED", "CANCELLED")):
            print("output model:", getattr(j, "output_model", None))
            break
        if args.once:
            break
        time.sleep(30)


def cmd_models(args):
    c = client(); aid = account_id(c)
    page = c.models.list(account_id=aid, page_size=50)
    for m in getattr(page, "models", []) or []:
        print(m.name, "|", getattr(m, "kind", ""), "|", getattr(m, "state", ""), "| base:", getattr(m, "base_model_details", None) and getattr(m.base_model_details, "parent_model", ""))


def cmd_deploy(args):
    c = client(); aid = account_id(c)
    model = args.model if args.model.startswith("accounts/") else f"accounts/{aid}/models/{args.model}"
    # Serverless LoRA: load the addon onto Fireworks' own deployment of the base model.
    try:
        r = c.lora.load(account_id=aid, model=model, **({"deployment": args.deployment} if args.deployment else {"serverless": True}))
        print("loaded:", r)
    except Exception as e:
        print(f"lora.load failed ({e!r}). If the base has no serverless LoRA support, create an on-demand deployment with\n"
              f"  --enable_addons on the base model, then pass --deployment accounts/{aid}/deployments/<id>.")
        return
    print(f"serve name to use with bench/infer.py: {model}  (check `models` for the exact deployed model id)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("upload"); p.add_argument("file"); p.add_argument("dataset_id"); p.set_defaults(fn=cmd_upload)
    p = sub.add_parser("train"); p.add_argument("dataset"); p.add_argument("--eval"); p.add_argument("--base", default="accounts/fireworks/models/qwen3-8b")
    p.add_argument("--epochs", type=float, default=3); p.add_argument("--lr", type=float, default=1e-4); p.add_argument("--rank", type=int, default=16)
    p.add_argument("--out", default="atc-qwen3-8b-v2"); p.add_argument("--no-turbo", action="store_true"); p.add_argument("--max-ctx", type=int, default=0); p.set_defaults(fn=cmd_train)
    p = sub.add_parser("status"); p.add_argument("job_id"); p.add_argument("--once", action="store_true"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("models"); p.set_defaults(fn=cmd_models)
    p = sub.add_parser("deploy"); p.add_argument("model"); p.add_argument("--deployment"); p.set_defaults(fn=cmd_deploy)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
