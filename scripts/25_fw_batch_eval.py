#!/usr/bin/env python3
"""Frozen-test run through Fireworks *batch inference* — for a fine-tuned model whose base has no serverless LoRA and
no on-demand deployment config on this account (Nemotron-3-Nano-30B-A3B). Same system prompt, same few-shot pool
(train split), same max_tokens/temperature as bench/infer.py; the output is converted to the bench preds format so
bench/score.py treats it like every other arm.

  python3 scripts/25_fw_batch_eval.py submit  --model accounts/<acct>/models/<lora> --fewshot 0 --tag atc-nemotron-nano-30b-v1_fwbatch
  python3 scripts/25_fw_batch_eval.py submit  --model accounts/fireworks/models/nemotron-nano-3-30b-a3b --fewshot 5 --tag nemotron-nano-30b-base_fwbatch
  python3 scripts/25_fw_batch_eval.py collect --tag <tag>        # polls; writes results/test/<tag>_fs<N>.preds.jsonl when done
"""
import argparse, hashlib, json, os, sys, tempfile, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from infer import build_messages, load_jsonl  # noqa: E402
from fireworks import Fireworks  # noqa: E402

AID = os.environ.get("FIREWORKS_ACCOUNT_ID", "francolinjo-co18wqhx")


def client():
    return Fireworks(api_key=os.environ["FIREWORKS_API_KEY"])


def check_hash():
    h = hashlib.sha256(open("data/splits/test.jsonl", "rb").read()).hexdigest()
    want = open("data/splits/test.sha256").read().split()[0]
    assert h == want, "TEST SET HASH MISMATCH — stop"


def cmd_submit(a):
    check_hash()
    c = client()
    system = open("prompts/system.txt", encoding="utf-8").read().strip()
    rows = load_jsonl("data/splits/test.jsonl")
    shots = load_jsonl("data/splits/train.jsonl")[: a.fewshot] if a.fewshot else []
    extra = json.loads(a.extra) if a.extra else {}
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for r in rows:
        tmp.write(json.dumps({"custom_id": r["id"], "body": {"messages": build_messages(system, shots, r),
                                                               "max_tokens": a.max_tokens, "temperature": 0.0, **extra}}, ensure_ascii=False) + "\n")
    tmp.close()
    rid = (a.tag.replace("_", "-").lower() + f"-fs{a.fewshot}")   # Fireworks resource ids: lower-case letters, digits, hyphens; shot count keeps ids unique
    ds_in, ds_out = f"{rid}-in", f"{rid}-out"
    for did in (ds_in,):
        try:
            c.datasets.create(account_id=AID, dataset_id=did, dataset={"display_name": did, "example_count": len(rows)})
        except Exception as e:
            print("dataset create:", str(e)[:120])
        with open(tmp.name, "rb") as fh:
            c.datasets.upload(dataset_id=did, account_id=AID, file=fh)
        for _ in range(40):
            if str(getattr(c.datasets.get(dataset_id=did, account_id=AID), "state", "")).upper().endswith("READY"):
                break
            time.sleep(3)
    os.unlink(tmp.name)
    job = c.batch_inference_jobs.create(account_id=AID, batch_inference_job_id=rid, model=a.model,
                                        input_dataset_id=f"accounts/{AID}/datasets/{ds_in}",
                                        output_dataset_id=f"accounts/{AID}/datasets/{ds_out}",
                                        inference_parameters={"max_tokens": a.max_tokens, "temperature": 0.0, **({"extra_body": json.dumps(extra)} if extra else {})})
    print("job:", job.name, getattr(job, "state", ""))
    json.dump({"tag": a.tag, "model": a.model, "fewshot": a.fewshot, "job": job.name, "out": ds_out, "submitted": time.time()},
              open(f"results/test/{a.tag}_fs{a.fewshot}.batchjob.json", "w"), indent=1)


def cmd_collect(a):
    import requests
    c = client()
    metas = [json.load(open(p)) for p in os.listdir("results/test") if False]  # placeholder
    metas = [json.load(open(os.path.join("results/test", f))) for f in os.listdir("results/test") if f.startswith(a.tag) and f.endswith(".batchjob.json")]
    assert metas, "no batchjob.json for that tag"
    m = metas[0]
    while True:
        j = c.batch_inference_jobs.get(batch_inference_job_id=m["job"].split("/")[-1], account_id=AID)
        st = str(getattr(j, "state", ""))
        print(time.strftime("%H:%M:%S"), st, getattr(j, "status", "") or "")
        if any(s in st.upper() for s in ("COMPLETED", "FAILED", "CANCELLED", "EXPIRED")):
            break
        if a.once:
            return
        time.sleep(30)
    if "COMPLETED" not in st.upper():
        sys.exit("batch job did not complete")
    H = {"Authorization": f"Bearer {os.environ['FIREWORKS_API_KEY']}"}
    r = requests.get(f"https://api.fireworks.ai/v1/accounts/{AID}/datasets/{m['out']}:getDownloadEndpoint", headers=H, timeout=60)
    print("download endpoint:", r.status_code, r.text[:300])
    urls = r.json().get("filenameToSignedUrls", {})
    out = f"results/test/{a.tag}_fs{m['fewshot']}.preds.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for fn, u in urls.items():
            if "error" in fn.lower():
                continue
            txt = requests.get(u, timeout=120).text
            for l in txt.splitlines():
                if not l.strip():
                    continue
                d = json.loads(l)
                resp = d.get("response") or d.get("body") or d
                body = resp.get("body", resp) if isinstance(resp, dict) else {}
                try:
                    content = body["choices"][0]["message"].get("content") or ""
                except Exception:
                    content = ""
                usage = body.get("usage") or {}
                fh.write(json.dumps({"id": d.get("custom_id"), "model": m["model"], "output": content, "latency_ms": None,
                                     "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                                     "error": None if content else "empty"}, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {out} ({n} rows)")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("submit"); p.add_argument("--model", required=True); p.add_argument("--fewshot", type=int, default=0)
    p.add_argument("--tag", required=True); p.add_argument("--max-tokens", type=int, default=1500); p.add_argument("--extra"); p.set_defaults(fn=cmd_submit)
    p = sub.add_parser("collect"); p.add_argument("--tag", required=True); p.add_argument("--once", action="store_true"); p.set_defaults(fn=cmd_collect)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
