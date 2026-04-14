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

# ─── Stage 1: Save raw log (fast, inline) ───
# Read stdin, save to temp file in vault's .memo dir (not /tmp — avoids sensitive data in shared dirs)
MEMO_TMP_DIR="${VAULT_PATH}/.memo/tmp"
mkdir -p "$MEMO_TMP_DIR"
TMPFILE=$(mktemp "${MEMO_TMP_DIR}/auto_memo_input.XXXXXX.json")

# Clean up temp file on exit (handles all exit paths including Stage 2 failures)
cleanup() { rm -f "$TMPFILE"; }
trap cleanup EXIT

cat > "$TMPFILE"

python3 "$SCRIPT_DIR/save_raw_log.py" --vault "$VAULT_PATH" < "$TMPFILE" 2>/dev/null || true

# ─── Stage 2: Classify (detached, background) ───
# nohup + disown: survives Claude Code exit
# Copy tmpfile for background process since trap will clean the original
TMPFILE_BG=$(mktemp "${MEMO_TMP_DIR}/auto_memo_bg.XXXXXX.json")
cp "$TMPFILE" "$TMPFILE_BG"

nohup bash -c "python3 \"$SCRIPT_DIR/auto_memo.py\" --vault \"$VAULT_PATH\" < \"$TMPFILE_BG\" >> \"${VAULT_PATH}/.memo/auto_memo.log\" 2>&1; rm -f \"$TMPFILE_BG\"" &
disown

exit 0
