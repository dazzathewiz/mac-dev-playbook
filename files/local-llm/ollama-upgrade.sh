#!/bin/bash
# Managed by mac-dev-playbook — do not edit by hand.
#
# Weekly Ollama upgrade, run by launchd. Upgrades the Homebrew formula,
# restarts the server agent if the version changed, then smoke-tests it.
# Failures are logged and raise a notification. No rollback, and the script
# always exits 0.
set -uo pipefail

LABEL="${OLLAMA_SERVER_LABEL:-com.dazzathewiz.ollama}"
MODEL="${OLLAMA_SMOKE_MODEL:-qwen3.6:35b-a3b}"
API="http://127.0.0.1:11434"
LOG="$HOME/Library/Logs/ollama/upgrade.log"
PY=/usr/bin/python3

mkdir -p "$(dirname "$LOG")"
log() { printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$*" >>"$LOG"; }

fail() {
  local msg="$*"
  log "FAIL: $msg"
  msg="${msg//[\"\\]/}"
  /usr/bin/osascript -e "display notification \"${msg:0:200}\" with title \"Ollama upgrade\"" >/dev/null 2>&1
  exit 0
}

version() { brew list --versions ollama 2>/dev/null | awk '{print $2}'; }

wait_for_api() {
  for _ in $(seq 1 30); do
    curl -fsS --max-time 5 "$API/api/version" >/dev/null 2>&1 && return 0
    sleep 2
  done
  return 1
}

before="$(version)"
if ! out="$(brew upgrade ollama 2>&1)"; then
  log "$out"
  fail "brew upgrade ollama failed"
fi
after="$(version)"

if [ "$before" != "$after" ]; then
  log "upgraded ollama $before -> $after; restarting $LABEL"
  launchctl kickstart -k "gui/$(id -u)/$LABEL" >>"$LOG" 2>&1 || fail "kickstart of $LABEL failed"
else
  log "ollama $after already current"
fi

# --- Smoke test ---------------------------------------------------------

wait_for_api || fail "/api/version not responding"

body="$("$PY" -c 'import json,sys; print(json.dumps({
  "model": sys.argv[1], "stream": False, "think": False,
  "options": {"temperature": 0},
  "messages": [{"role": "user", "content": "Reply with ONLY this JSON object: {\"ok\": true}"}]}))' "$MODEL")"

reply="$(curl -fsS --max-time 600 "$API/api/chat" -H 'Content-Type: application/json' -d "$body" 2>&1)" \
  || fail "chat with $MODEL failed: $reply"

# The reply content must parse as a JSON object (code fences tolerated).
# shellcheck disable=SC2016  # the backticks are Python, not shell
printf '%s' "$reply" | "$PY" -c '
import json, re, sys
content = json.load(sys.stdin)["message"]["content"]
content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.M).strip()
assert isinstance(json.loads(content), dict)
' 2>/dev/null || fail "chat with $MODEL did not return parseable JSON"

runner="$(curl -fsS --max-time 10 "$API/api/ps" 2>/dev/null | "$PY" -c '
import json, sys
m = [x for x in json.load(sys.stdin).get("models", []) if x.get("name") == sys.argv[1]]
print(m[0].get("runner", "") if m else "")
' "$MODEL" 2>/dev/null)"
[ "$runner" = "mlx" ] || fail "$MODEL runner is '${runner:-not loaded}', expected mlx"

log "PASS: ollama $after, $MODEL answered JSON on the mlx runner"
exit 0
