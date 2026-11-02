#!/usr/bin/env python3
"""Live DGX Spark parser proxy for the runway monitor.

  python3 viz/live_server.py            # then open http://localhost:8090/?live=1

Serves viz/ as static files and adds two endpoints:
  POST /parse  {"text": "...", "facility": "san francisco tower"}
       -> calls the vLLM server on :8001 (runs/qwen3-8b-atc/merged, served as "student") with the exact system
          prompt in prompts/system.txt and the exact user-message format of bench/make_sft.user_message,
          0-shot, temperature 0, max_tokens 300, enable_thinking false. Returns the parsed JSON, wall-clock
          latency (measured here, same machine), tokens in/out and the served model name.
  GET  /gpu    -> latest `nvidia-smi --query-gpu=utilization.gpu,memory.used` line + util history, polled every 1 s.
  GET  /endpoints -> the three model servers (:8001 LoRA, :8002 Lightning, :8004 base) with an up flag (polled every 3 s).
  POST /parse_on {"port": 8002, "text": ...} -> same request to any of the three (Spark view load test).
Stdlib only. Env: VLLM_URL (default http://localhost:8001/v1), MODEL (default "student"), PORT (default 8090).
"""
import json, os, subprocess, sys, threading, time, urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bench"))
from make_sft import user_message  # noqa: E402  (same formatting as training and eval)

VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8001/v1")
MODEL = os.environ.get("MODEL", "student")
PORT = int(os.environ.get("PORT", "8090"))
SYSTEM = open(os.path.join(ROOT, "prompts", "system.txt")).read().strip()
GPU = {"line": "n/a", "at": 0.0, "util": None, "hist": []}   # hist: [(unix_s, util%)], last 120 s at 1 s
ENDPOINTS = [  # the three model servers on this Spark, shown in the Spark view with an up/down light
    {"port": 8001, "name": "Qwen3-8B + GMAPS LoRA (merged, bf16)", "model": "student"},
    {"port": 8002, "name": "Nemotron-3.5-Lightning-30B-A3B NVFP4", "model": "nemotron-lightning-3.5-30b"},
    {"port": 8004, "name": "Qwen3-8B off the shelf (bf16)", "model": "qwen3-8b-base"},
]
UP = {}


def poll_gpu():
    while True:
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            if "N/A" in out:  # GB10 unified memory: memory.used is not reported; add up the GPU processes instead
                apps = subprocess.run(["nvidia-smi", "--query-compute-apps=used_memory", "--format=csv,noheader,nounits"],
                                      capture_output=True, text=True, timeout=5).stdout.split()
                mib = sum(int(x) for x in apps if x.isdigit())
                out = f"{out.split(',')[0].strip()} · GPU procs {mib / 1024:.1f} GiB (unified)"
            GPU.update(line=out or "n/a", at=time.time())
            util = out.split("%")[0].strip()
            GPU["util"] = int(util) if util.isdigit() else None
            if GPU["util"] is not None:
                GPU["hist"] = (GPU["hist"] + [(round(time.time(), 1), GPU["util"])])[-120:]
        except Exception as e:  # noqa: BLE001
            GPU.update(line=f"nvidia-smi error: {e}", at=time.time())
        time.sleep(1)


def poll_endpoints():
    while True:
        for e in ENDPOINTS:
            try:
                with urllib.request.urlopen(f"http://localhost:{e['port']}/v1/models", timeout=2) as r:
                    UP[e["port"]] = r.status == 200
            except Exception:  # noqa: BLE001
                UP[e["port"]] = False
        time.sleep(3)


def parse_on(port, model, text, facility, extra):
    """Same request shape as parse(), to any of the three endpoints (used by the Spark view's load test)."""
    payload = {"model": model, "temperature": 0, "max_tokens": 300,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": user_message({"facility": facility, "text": text})}], **extra}
    req = urllib.request.Request(f"http://localhost:{port}/v1/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer none"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    u = resp.get("usage", {})
    return {"port": port, "model": model, "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens"),
            "output": resp["choices"][0]["message"].get("content") or ""}


def parse(text, facility):
    payload = {"model": MODEL, "temperature": 0, "max_tokens": 300,
               "chat_template_kwargs": {"enable_thinking": False},
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": user_message({"facility": facility, "text": text})}]}
    req = urllib.request.Request(VLLM_URL + "/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer none"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    ms = (time.perf_counter() - t0) * 1000
    content = resp["choices"][0]["message"].get("content") or ""
    try:
        parsed, ok = json.loads(content), True
    except json.JSONDecodeError:
        parsed, ok = content, False
    u = resp.get("usage", {})
    return {"model": resp.get("model", MODEL), "parsed": parsed, "json_valid": ok, "latency_ms": round(ms, 1),
            "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens")}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if "/gpu" not in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/gpu"):
            return self._json({"gpu": GPU["line"], "util": GPU["util"], "hist": GPU["hist"][-60:], "age_s": round(time.time() - GPU["at"], 1)})
        if self.path.startswith("/endpoints"):
            return self._json([{**e, "up": UP.get(e["port"], False)} for e in ENDPOINTS])
        return super().do_GET()

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path.startswith("/parse_on"):
            e = next((e for e in ENDPOINTS if e["port"] == int(req.get("port", 0))), None)
            if not e:
                return self._json({"error": "unknown port"}, 400)
            extra = {"chat_template_kwargs": {"enable_thinking": False}} if "qwen" in e["model"] or e["model"] == "student" else {"reasoning_effort": "none"}
            try:
                return self._json(parse_on(e["port"], e["model"], req["text"], req.get("facility", "laguardia tower"), extra))
            except Exception as ex:  # noqa: BLE001
                return self._json({"error": str(ex), "port": e["port"]}, 502)
        if not self.path.startswith("/parse"):
            return self._json({"error": "not found"}, 404)
        try:
            res = parse(req["text"], req.get("facility", "san francisco tower"))
            print(f"[parse] {res['latency_ms']:.0f} ms  in={res['tokens_in']} out={res['tokens_out']}  {req['text'][:60]}", flush=True)
            return self._json(res)
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 502)


if __name__ == "__main__":
    threading.Thread(target=poll_gpu, daemon=True).start()
    threading.Thread(target=poll_endpoints, daemon=True).start()
    print(f"live parser proxy on http://localhost:{PORT}/  ->  {VLLM_URL} model={MODEL}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), partial(Handler, directory=HERE)).serve_forever()
