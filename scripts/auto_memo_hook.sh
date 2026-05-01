#!/usr/bin/env bash
# auto_memo_hook.sh — SessionEnd hook (two-stage pipeline).
#
# Stage 1 (inline, fast): Save raw daily log. No API calls.
#   → Captures last 30 messages as markdown in daily-logs/
#   → Runs in <1s, safe within SessionEnd timeout
#
# Stage 2 (detached, background): Classify and create structured memos.
#   → nohup + disown so it survives Claude Code exit
#   → Calls Haiku API to classify transcript
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
# SessionEnd payload schema empirically. Disabled by default — no on-disk
# capture without the explicit env var.
#
# Usage in settings.json:
#   "SessionEnd": [{
#     "matcher": "*",
#     "hooks": [{
#       "type": "command",
#       "command": "bash ~/.claude/skills/memo-skill/scripts/auto_memo_hook.sh"
#     }]
#   }]
#   Set MEMO_VAULT_PATH env var to override default ~/memo-vault.

set -euo pipefail

VAULT_PATH="${MEMO_VAULT_PATH:-$HOME/memo-vault}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read stdin into temp file in vault's .memo dir (not /tmp — avoids sensitive data in shared dirs)
MEMO_TMP_DIR="${VAULT_PATH}/.memo/tmp"
mkdir -p "$MEMO_TMP_DIR"
TMPFILE=$(mktemp "${MEMO_TMP_DIR}/auto_memo_input.XXXXXX.json")

# Clean up temp file on exit (handles all exit paths including Stage 2 failures)
cleanup() { rm -f "$TMPFILE"; }
trap cleanup EXIT

cat > "$TMPFILE"

# ─── Extract transcript_path from payload (no jq, no external deps) ───
# Use stdin redirection rather than -c arg to avoid ARG_MAX edge cases and
# to keep payload bytes out of `ps` output. The python3 -c parser handles:
#   - missing field          (defaults to empty string)
#   - non-string field type  (skipped — print empty)
#   - JSON decode error      (caught, prints empty)
#   - non-dict top-level     (caught, prints empty)
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
# stat -f%z (BSD/macOS) is tried first; -c%s (GNU/Linux) is the fallback so
# the same hook works on either platform with no external deps.
TRANSCRIPT_EXISTS="false"
TRANSCRIPT_SIZE=0
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    TRANSCRIPT_EXISTS="true"
    TRANSCRIPT_SIZE=$(stat -f%z "$TRANSCRIPT_PATH" 2>/dev/null || stat -c%s "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
fi

# ─── MEMO_DEBUG payload capture (independent of gate; captures every payload) ───
# Single >> redirect on python3 — POSIX guarantees O_APPEND writes <= PIPE_BUF
# (4096 bytes on macOS) are atomic, so concurrent SessionEnd hooks cannot
# interleave their JSONL lines. Our wrapper line is well under that bound.
if [ "${MEMO_DEBUG:-0}" = "1" ]; then
    DEBUG_FILE="${VAULT_PATH}/.memo/hook_payloads.jsonl"
    mkdir -p "$(dirname "$DEBUG_FILE")"
    python3 -c '
import json, sys
from datetime import datetime
try:
    raw = open(sys.argv[1], "r", encoding="utf-8").read()
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"_raw": raw}
    wrapper = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "transcript_exists": sys.argv[2] == "true",
        "transcript_size": int(sys.argv[3]),
        "payload": payload,
    }
    print(json.dumps(wrapper, ensure_ascii=False))
except Exception:
    pass
' "$TMPFILE" "$TRANSCRIPT_EXISTS" "$TRANSCRIPT_SIZE" >> "$DEBUG_FILE" 2>/dev/null || true
fi

# ─── Gate: subagent / phantom event → silent exit ───
# Threshold rationale: see top-of-file comment. Mirrored in save_raw_log.py.
if [ "$TRANSCRIPT_EXISTS" != "true" ] || [ "$TRANSCRIPT_SIZE" -lt 2048 ]; then
    exit 0
fi

# ─── Stage 1: Save raw log (fast, inline) ───
# Capture exit code so Stage 2 can be gated on success. set -euo pipefail is
# in effect, so the if/then pattern is the correct way to capture a non-zero
# exit without aborting the script.
if python3 "$SCRIPT_DIR/save_raw_log.py" --vault "$VAULT_PATH" < "$TMPFILE" 2>/dev/null; then
    STAGE1_OK=1
else
    STAGE1_OK=0
fi

# ─── Stage 2: Classify (detached, background) ───
# Only run if Stage 1 succeeded. nohup + disown: survives Claude Code exit.
# Copy tmpfile for background process since trap cleans the original.
if [ "$STAGE1_OK" = "1" ]; then
    TMPFILE_BG=$(mktemp "${MEMO_TMP_DIR}/auto_memo_bg.XXXXXX.json")
    cp "$TMPFILE" "$TMPFILE_BG"

    nohup bash -c "python3 \"$SCRIPT_DIR/auto_memo.py\" --vault \"$VAULT_PATH\" < \"$TMPFILE_BG\" >> \"${VAULT_PATH}/.memo/auto_memo.log\" 2>&1; rm -f \"$TMPFILE_BG\"" &
    disown
fi

exit 0
