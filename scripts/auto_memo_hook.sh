#!/usr/bin/env bash
# auto_memo_hook.sh — SessionEnd hook (two-stage pipeline).
#
# Stage 1 (inline, fast): Save raw daily log. No API calls.
#   → Captures last 30 messages as markdown in daily-logs/
#   → Runs in <1s, safe within SessionEnd timeout
#
# Stage 2 (detached, background): Classify and create structured memos.
#   → Launcher shim + nohup so it survives Claude Code exit
#   → Calls LLM to classify transcript
#   → Creates structured memo articles in vault
#
# The compile_logs.py cron job also processes daily logs → articles.
# Stage 2 here is optional extra — catches things immediately.
# If it fails, compile_logs.py will pick them up later.
#
# ─── Subagent / phantom-event gate ───
# Claude Code fires SessionEnd for both real sessions and Task-tool subagents,
# but the payload schema does not expose a main-vs-subagent flag. We use
# filesystem evidence instead: a real session has an existing transcript file
# of >= 2048 bytes; subagent transcripts are missing or empty/header-only.
#
# Threshold rationale: 2048 bytes is below the floor of any real session we
# care about (a 4-message exchange in Claude Code's nested JSONL format is
# typically 3-5 KB because each entry includes metadata + tool blocks +
# timestamps). It comfortably filters empty / header-only subagent transcripts
# while passing genuinely short real sessions through.
#
# The same threshold is duplicated in scripts/save_raw_log.py as defense-in-depth
# for direct invocation outside the hook. If the threshold changes, both files
# must be updated in the same commit.
#
# ─── MEMO_DEBUG opt-in payload capture ───
# Set MEMO_DEBUG=1 in the environment to append every SessionEnd payload
# (including rejected/subagent ones) as a single JSONL line to
# `${VAULT_PATH}/.memo/hook_payloads.jsonl`. Used to reverse-engineer the
# SessionEnd payload schema empirically. Disabled by default.
#
# SECURITY: when MEMO_DEBUG=1 is on, hook_payloads.jsonl is created with
# mode 0600, secrets in tool_use blocks are redacted before write, and the
# file is rotated at 10MB. See REDACT_PY below for the patterns matched.
#
# Usage in settings.json:
#   "SessionEnd": [{
#     "hooks": [{
#       "type": "command",
#       "command": "bash /path/to/auto_memo_hook.sh"
#     }]
#   }]
#   Set MEMO_VAULT_PATH env var to override default ~/memo-vault.

set -euo pipefail

VAULT_PATH="${MEMO_VAULT_PATH:-$HOME/memo-vault}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Per-vault cache lives outside the vault — keeps Dropbox / iCloud from
# syncing SQLite WAL sidecars, lock files, and debug captures. The
# Python helper resolves + auto-migrates legacy `<vault>/.memo/` on
# first run.
MEMO_DIR="$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from memo_utils import get_memo_dir
print(get_memo_dir('$VAULT_PATH'))
" 2>/dev/null)"
if [ -z "$MEMO_DIR" ]; then
    # Fallback if Python or memo_utils unavailable. Keep working but
    # warn — the orig path location stays consistent for this run.
    echo "[memo] WARN: could not resolve memo cache dir; falling back to vault-local .memo/" >&2
    MEMO_DIR="${VAULT_PATH}/.memo"
fi

MEMO_TMP_DIR="$MEMO_DIR/tmp"
mkdir -p "$MEMO_TMP_DIR"
chmod 700 "$MEMO_TMP_DIR" 2>/dev/null || true

# ─── Sweep stale temp files at hook entry (H-ROB-4) ───
# nohup'd Stage 2 may be killed by SIGTERM before its `rm -f` runs.
# Older than 60min is safely orphaned (Haiku timeout is 120s).
find "$MEMO_TMP_DIR" -maxdepth 1 -type f \( -name 'auto_memo_input.*.json' -o -name 'auto_memo_bg.*.json' -o -name 'auto_memo_launcher.*.sh' \) -mmin +60 -delete 2>/dev/null || true

TMPFILE=$(mktemp "${MEMO_TMP_DIR}/auto_memo_input.XXXXXX.json")
chmod 600 "$TMPFILE" 2>/dev/null || true

# Clean up temp file on exit (handles all exit paths including Stage 2 failures)
cleanup() { rm -f "$TMPFILE"; }
trap cleanup EXIT

cat > "$TMPFILE"

# ─── Extract transcript_path from payload (no jq, no external deps) ───
TRANSCRIPT_PATH=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        v = data.get("transcript_path", "")
        if isinstance(v, str):
            print(v)
except Exception:
    pass
' < "$TMPFILE" 2>/dev/null || true)

# ─── Determine transcript existence and size ───
TRANSCRIPT_EXISTS="false"
TRANSCRIPT_SIZE=0
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    TRANSCRIPT_EXISTS="true"
    TRANSCRIPT_SIZE=$(stat -f%z "$TRANSCRIPT_PATH" 2>/dev/null || stat -c%s "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
fi

# ─── MEMO_DEBUG payload capture (CR-1 + N-H-C hardened) ───
#
# Why fcntl, not `>>`:
#   POSIX makes NO atomicity guarantee for write() on regular files. The old
#   single-`>>` redirect assumption (and the PIPE_BUF comment that justified
#   it) was wrong: PIPE_BUF only applies to pipes/FIFOs. The Python child
#   below acquires fcntl.LOCK_EX on the debug file before writing — concurrent
#   SessionEnd hooks serialize cleanly.
#
# Security:
#   - File pre-created with umask 077 (mode 0600); reset every run.
#   - Redaction: tool_use args matching common secret patterns are masked
#     before write. Defense in depth, not a substitute for `MEMO_DEBUG=0`.
#   - Rotation: file is renamed to .1 when it crosses 10MB, then a fresh
#     file is created. We keep at most one rotated copy.
#   - Stderr banner reminds the user the capture is on.

if [ "${MEMO_DEBUG:-0}" = "1" ]; then
    DEBUG_FILE="$MEMO_DIR/hook_payloads.jsonl"
    echo "[memo] MEMO_DEBUG=1 — appending payload to $DEBUG_FILE (mode 0600, redacted, rotated at 10MB)" >&2
    mkdir -p "$(dirname "$DEBUG_FILE")"

    # Pre-create with restrictive mode if missing; correct mode on every run
    # so manual chmod doesn't drift.
    if [ ! -e "$DEBUG_FILE" ]; then
        (umask 077 && : > "$DEBUG_FILE")
    fi
    chmod 600 "$DEBUG_FILE" 2>/dev/null || true

    python3 - "$TMPFILE" "$TRANSCRIPT_EXISTS" "$TRANSCRIPT_SIZE" "$DEBUG_FILE" <<'PY' || true
import fcntl, json, os, re, sys
from datetime import datetime

ROTATE_BYTES = 10 * 1024 * 1024  # 10MB
SECRET_KEY_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|apikey|authorization|auth[_-]?token|bearer|token|password|passwd|secret|client[_-]?secret|private[_-]?key|aws[_-]?(access|secret)[_-]?key[_-]?id?)\b"
)
SECRET_VALUE_PATTERN = re.compile(
    r"\b(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|aws_[a-z_]+=[A-Za-z0-9/+=]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)


def redact(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and SECRET_KEY_PATTERN.search(k):
                out[k] = "[REDACTED]"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    if isinstance(obj, str):
        return SECRET_VALUE_PATTERN.sub("[REDACTED]", obj)
    return obj


try:
    tmpfile, exists, size, debug_file = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    with open(tmpfile, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"_raw": raw[:4096]}

    payload = redact(payload)
    wrapper = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "transcript_exists": exists == "true",
        "transcript_size": int(size),
        "payload": payload,
    }
    line = json.dumps(wrapper, ensure_ascii=False) + "\n"

    # Rotate before write if file is already big
    try:
        if os.path.getsize(debug_file) + len(line.encode("utf-8")) > ROTATE_BYTES:
            os.replace(debug_file, debug_file + ".1")
    except OSError:
        pass

    fd = os.open(debug_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
except Exception:
    pass
PY
fi

# ─── Gate: subagent / phantom event → silent exit ───
if [ "$TRANSCRIPT_EXISTS" != "true" ] || [ "$TRANSCRIPT_SIZE" -lt 2048 ]; then
    exit 0
fi

# ─── Stage 1: Save raw log (fast, inline) ───
if python3 "$SCRIPT_DIR/save_raw_log.py" --vault "$VAULT_PATH" < "$TMPFILE" 2>/dev/null; then
    STAGE1_OK=1
else
    STAGE1_OK=0
fi

# ─── Stage 2: Classify (detached, background) via launcher shim (N-H-D) ───
#
# Why a shim and not `nohup bash -c "..."`:
#   The old version interpolated $SCRIPT_DIR, $VAULT_PATH, $TMPFILE_BG into a
#   double-quoted string passed to `bash -c`. The outer shell parsed those vars
#   BEFORE bash -c saw them — if any contained quotes/$/backticks, the string
#   broke or executed arbitrary code under the user UID. The launcher takes
#   args via argv, never through the shell.
if [ "$STAGE1_OK" = "1" ]; then
    TMPFILE_BG=$(mktemp "${MEMO_TMP_DIR}/auto_memo_bg.XXXXXX.json")
    chmod 600 "$TMPFILE_BG" 2>/dev/null || true
    cp "$TMPFILE" "$TMPFILE_BG"

    LAUNCHER=$(mktemp "${MEMO_TMP_DIR}/auto_memo_launcher.XXXXXX.sh")
    cat > "$LAUNCHER" <<'LAUNCHER_SH'
#!/usr/bin/env bash
# Generated by auto_memo_hook.sh — self-cleans after run
set -uo pipefail
PYBIN="$1"; SCRIPT="$2"; VAULT="$3"; STDIN_FILE="$4"; LOG="$5"; SELF="$6"
"$PYBIN" "$SCRIPT" --vault "$VAULT" < "$STDIN_FILE" >> "$LOG" 2>&1
rm -f "$STDIN_FILE" "$SELF"
LAUNCHER_SH
    chmod 755 "$LAUNCHER"

    PYBIN="$(command -v python3)"
    nohup "$LAUNCHER" \
        "$PYBIN" \
        "$SCRIPT_DIR/auto_memo.py" \
        "$VAULT_PATH" \
        "$TMPFILE_BG" \
        "$MEMO_DIR/auto_memo.log" \
        "$LAUNCHER" \
        >/dev/null 2>&1 &
    disown
fi

exit 0
