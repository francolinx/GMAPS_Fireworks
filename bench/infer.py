#!/usr/bin/env python3
"""Run one model over a split through any OpenAI-compatible chat endpoint, logging latency and tokens.

Works unchanged for the closed baseline and the open models:
  # Fireworks (open models, fine-tuned LoRAs)
  BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY=$FIREWORKS_API_KEY \
    python bench/infer.py --model accounts/fireworks/models/qwen3-8b --split data/splits/test.jsonl \
    --out results/preds_qwen3_base.jsonl --fewshot 5

  # OpenAI
  BASE_URL=https://api.openai.com/v1 API_KEY=$OPENAI_API_KEY python bench/infer.py --model gpt-5 ...

  # Anthropic (OpenAI-compatible endpoint)
  BASE_URL=https://api.anthropic.com/v1 API_KEY=$ANTHROPIC_API_KEY python bench/infer.py --model claude-... ...

  # local vLLM / llama.cpp on the Spark
  BASE_URL=http://spark-6771:8000/v1 API_KEY=none python bench/infer.py --model <served-name> ...

Few-shot examples come from the DEV split (never test) and are identical for every arm.
Latency is wall-clock per request, measured client-side, same machine for every arm.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from make_sft import user_message, target  # noqa: E402


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def build_messages(system, shots, row):
    msgs = [{"role": "system", "content": system}]
    for s in shots:
        msgs.append({"role": "user", "content": user_message(s)})
        msgs.append({"role": "assistant", "content": json.dumps(target(s), ensure_ascii=False)})
    msgs.append({"role": "user", "content": user_message(row)})
    return msgs


def call(base_url, api_key, payload, timeout, retries=3):
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    last = None
    for attempt in range(retries):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            ms = (time.perf_counter() - t0) * 1000
            choice = body["choices"][0]["message"]
            content = choice.get("content") or ""
            usage = body.get("usage") or {}
            return content, ms, usage.get("prompt_tokens"), usage.get("completion_tokens"), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}"
            if e.code in (429, 500, 502, 503, 529):
                time.sleep(1.5 * (attempt + 1))
                continue
            break
        except Exception as e:  # timeouts, connection resets
            last = repr(e)
            time.sleep(1.5 * (attempt + 1))
    return "", None, None, None, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--split", default="data/splits/test.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--system", default="prompts/system.txt")
    ap.add_argument("--fewshot", type=int, default=0, help="N examples from --fewshot-from (dev split)")
    ap.add_argument("--fewshot-from", default="data/splits/dev.jsonl")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=300)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--json-mode", action="store_true", help='send response_format={"type":"json_object"}')
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--limit", type=int, default=0, help="only the first N rows (smoke test)")
    ap.add_argument("--extra", help="JSON of extra request fields (e.g. reasoning settings)")
    args = ap.parse_args()

    base_url, api_key = os.environ.get("BASE_URL"), os.environ.get("API_KEY")
    if not base_url or not api_key:
        sys.exit("set BASE_URL and API_KEY in the environment")

    system = open(args.system, encoding="utf-8").read().strip()
    rows = load_jsonl(args.split)
    if args.limit:
        rows = rows[: args.limit]
    shots = load_jsonl(args.fewshot_from)[: args.fewshot] if args.fewshot else []
    extra = json.loads(args.extra) if args.extra else {}

    done = {}
    if os.path.exists(args.out):  # resume
        for r in load_jsonl(args.out):
            done[r["id"]] = r
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(rows)} rows, {len(done)} already done, {len(todo)} to run → {args.model}")

    def work(row):
        payload = {
            "model": args.model,
            "messages": build_messages(system, shots, row),
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            **extra,
        }
        if args.json_mode:
            payload["response_format"] = {"type": "json_object"}
        content, ms, pt, ct, err = call(base_url, api_key, payload, args.timeout)
        return {"id": row["id"], "model": args.model, "output": content, "latency_ms": ms,
                "prompt_tokens": pt, "completion_tokens": ct, "error": err}

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    errors = 0
    with open(args.out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(args.concurrency) as ex:
        futs = [ex.submit(work, r) for r in todo]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            errors += bool(r["error"])
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} done, {errors} errors")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
