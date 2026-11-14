#!/usr/bin/env python3
"""Mac check-in for the n8n triage queue. Advisory only; fails open.

Every failure path exits 0 and does nothing: no n8n, no model server, low
battery, memory pressure, another run in progress. n8n owns the queue, leases
and validation; this client only claims, infers, pre-validates and submits.

  checkin.py                     # normal run (launchd)
  checkin.py --dry-run JOB.json  # infer on a local job file, print, no n8n
"""
import fcntl, json, os, re, socket, subprocess, sys, threading, time, urllib.request
from pathlib import Path

N8N = os.environ.get("TRIAGE_N8N_URL", "")  # triage webhook base URL
OLLAMA = os.environ.get("TRIAGE_OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("TRIAGE_MODEL", "qwen3.6:35b-a3b")
KEYCHAIN_SERVICE = "pr-triage-n8n"
MAX_JOBS, BUDGET_S, INFER_TIMEOUT_S, HEARTBEAT_S = 3, 25 * 60, 8 * 60, 5 * 60
MIN_BATTERY, MIN_FREE_MEM_PCT = 40, 25
LOG = Path.home() / "Library/Logs/pr-triage/checkin.log"
LOCK = Path.home() / "Library/Caches/pr-triage.lock"

SYSTEM = """You review one dependency-update PR for a home Kubernetes GitOps repo. Advisory only; a human merges.
Deterministic rule findings are included; do not contradict a rule marked blocked.
Reply with ONLY JSON: {"verdict":"low|review|block","confidence":0.0-1.0,
"reasons":[{"code":"kebab-case","evidence":"<exact quote copied from the payload>"}],"summary":"<=600 chars"}
Evidence rules: give at most 3 reasons. Each evidence string must be ONE complete line or sentence copied character-for-character from the payload, keeping backticks, markdown and arrows exactly as written. Never shorten with '...', never paraphrase, never join lines. If unsure, choose review."""
# Not sent: Ollama's MLX runner rejects "format" (501). Kept as the shape n8n validates.
SCHEMA = {"type": "object", "required": ["verdict", "confidence", "reasons", "summary"],
          "properties": {"verdict": {"enum": ["low", "review", "block"]}, "confidence": {"type": "number"},
                         "reasons": {"type": "array", "items": {"type": "object", "required": ["code", "evidence"],
                                     "properties": {"code": {"type": "string"}, "evidence": {"type": "string"}}}},
                         "summary": {"type": "string"}}}


def log(msg):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 5_000_000:
            LOG.write_text("")
        with LOG.open("a") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg + "\n")
    except Exception:
        pass


def http(method, url, body=None, token=None, timeout=10):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, timeout=10).stdout


def preflight():
    batt = sh("pmset", "-g", "batt")
    if "Battery Power" in batt:
        m = re.search(r"(\d+)%", batt)
        if m and int(m.group(1)) < MIN_BATTERY:
            return "battery low"
    tags = http("GET", OLLAMA + "/api/tags", timeout=3)
    model = next((m for m in tags.get("models", []) if m["name"] == MODEL), None)
    if not model:
        return "model not present locally"
    if "cloud" in MODEL or model.get("remote_host") or model.get("remote_model"):
        return "refusing a cloud/remote model"
    loaded = any(m["name"] == MODEL for m in http("GET", OLLAMA + "/api/ps", timeout=3).get("models", []))
    free = sh("sysctl", "-n", "kern.memorystatus_level").strip()
    if not loaded and free.isdigit() and int(free) < MIN_FREE_MEM_PCT:
        return "memory pressure (free %s%%)" % free
    return model.get("digest", "")


def extract_json(s):
    """Parse a JSON object from model text (fences/prose tolerated). None if absent."""
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    try:
        return json.loads(s)
    except ValueError:
        pass
    start = s.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(s)):
            depth += {"{": 1, "}": -1}.get(s[i], 0)
            if depth == 0:
                try:
                    return json.loads(s[start:i + 1])
                except ValueError:
                    break
        start = s.find("{", start + 1)
    return None


def infer(payload_text):
    body = {"model": MODEL, "stream": False, "think": False, "keep_alive": "10m",
            "options": {"temperature": 0, "num_ctx": 32768},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": payload_text}]}
    d = http("POST", OLLAMA + "/api/chat", body, timeout=INFER_TIMEOUT_S)
    out = extract_json(d.get("message", {}).get("content", ""))
    return out if isinstance(out, dict) else {}


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def prevalidate(out, payload_text):
    if out.get("verdict") not in ("low", "review", "block"):
        return None
    p = norm(payload_text)
    out["reasons"] = [r for r in out.get("reasons", [])
                      if len(r.get("evidence", "")) > 3 and norm(r["evidence"]) in p]
    if not out["reasons"]:
        return None
    out["summary"] = str(out.get("summary", ""))[:600]
    out["confidence"] = max(0.0, min(1.0, float(out.get("confidence", 0))))
    return out


def payload_text(job):
    p = job["payload"]
    return p if isinstance(p, str) else json.dumps(p, indent=1)


def heartbeat(token, lease, stop):
    while not stop.wait(HEARTBEAT_S):
        try:
            http("POST", N8N + "/heartbeat", {"lease_token": lease}, token, timeout=10)
        except Exception as e:
            log("heartbeat failed: %s" % e)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--dry-run":
        job = json.loads(Path(sys.argv[2]).read_text())
        txt = payload_text(job)
        print(json.dumps(prevalidate(infer(txt), txt), indent=1))
        return
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lockf = LOCK.open("w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    if not N8N:
        return
    start = time.time()
    try:
        digest = preflight()
    except Exception as e:
        log("skip: model server unreachable (%s)" % e)
        return
    if digest in ("battery low", "model not present locally", "refusing a cloud/remote model") or digest.startswith("memory"):
        log("skip: " + digest)
        return
    try:
        token = sh("security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w").strip()
        if not token:
            log("skip: no token in Keychain")
            return
        claim = http("POST", N8N + "/claim", {"device": socket.gethostname(), "max": MAX_JOBS}, token, timeout=8)
    except Exception as e:
        log("skip: n8n unreachable (%s)" % e)
        return
    jobs, lease = claim.get("jobs", []), claim.get("lease_token")
    if not jobs:
        return
    caff = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    stop = threading.Event()
    threading.Thread(target=heartbeat, args=(token, lease, stop), daemon=True).start()
    try:
        for job in jobs:
            if time.time() - start > BUDGET_S - INFER_TIMEOUT_S:
                log("budget spent; leaving %s to lease expiry" % job["id"])
                break
            txt = payload_text(job)
            t = time.time()
            try:
                raw = infer(txt)
                if raw.get("verdict") not in ("low", "review", "block"):
                    raw = infer(txt)
                out = prevalidate(raw, txt)
            except Exception as e:
                log("job %s inference failed: %s" % (job["id"], e))
                continue
            if out is None:
                log("job %s: no valid verdict/evidence; not submitted" % job["id"])
                continue
            out.update({"job_id": job["id"], "lease_token": lease, "head_sha": job["head_sha"],
                        "model": MODEL, "model_digest": digest})
            try:
                http("POST", N8N + "/result", out, token, timeout=15)
                log("job %s pr %s -> %s (%.0fs)" % (job["id"], job.get("pr"), out["verdict"], time.time() - t))
            except Exception as e:
                log("job %s submit failed: %s" % (job["id"], e))
    finally:
        stop.set()
        caff.terminate()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("unexpected: %r" % e)
    sys.exit(0)
