#!/usr/bin/env python3
"""
pre_compact_save.py — PreCompact hook.

When Claude Code auto-compacts the context window mid-session,
it discards details. This hook fires BEFORE compaction, grabs the
last N messages, and saves them as a raw daily log — same logic
as session_end, but triggered by compaction instead of exit.

This is the "insurance policy" for long sessions where important
decisions from the first hour get lost when Claude compacts at hour 3.

Runs synchronously (PreCompact waits for hooks), so keep it fast.
No API calls — just dump messages to a raw log file.
"""

import json
import os
import sys
from collections import deque
from datetime import datetime

# Threshold mirrors auto_memo_hook.sh — see that file for rationale.
_MIN_TRANSCRIPT_BYTES = 2048


def _log_precompact_error(message: str) -> None:
    """Log a PreCompact failure to ~/.cache/memo/precompact.log.

    sys.exit(1) without a log line makes a broken PreCompact hook
    invisible to the user — Claude Code swallows hook stderr. The
    cache location works even when the vault path is what's broken.
    """
    try:
        log_dir = os.path.expanduser("~/.cache/memo")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "precompact.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")
    except OSError:
        pass


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    session_id = hook_input.get("session_id", "unknown")

    # Add scripts dir to path for memo_utils import
    sys.path.insert(0, os.path.dirname(__file__))
    from memo_utils import daily_log_write, resolve_vault_path

    # Wrap resolve_vault_path so a missing MEMO_VAULT_PATH does not
    # silently sys.exit(1) — Claude Code swallows hook stderr, so the
    # user would have no idea PreCompact is broken. Log to the cache
    # log path instead.
    try:
        vault_path = resolve_vault_path(sys.argv)
    except SystemExit:
        _log_precompact_error("resolve_vault_path failed — set MEMO_VAULT_PATH or pass --vault")
        sys.exit(0)

    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    # Defense-in-depth size gate (symmetric with save_raw_log.py and
    # auto_memo_hook.sh). Subagent / phantom PreCompact events would
    # otherwise execute the full transcript read on every fire.
    try:
        if os.path.getsize(transcript_path) < _MIN_TRANSCRIPT_BYTES:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    # Read tail of transcript via deque — O(maxlen) memory, single-pass
    # streaming, safe on 200 MB transcripts.
    messages = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            tail = deque(f, maxlen=60)
    except (OSError, UnicodeDecodeError):
        sys.exit(0)

    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        # Handle Claude Code nested format
        if "message" in entry and isinstance(entry["message"], dict):
            entry = entry["message"]
        role = entry.get("role", "")
        content = entry.get("content", "")
        if isinstance(content, list):
            content = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        if role in ("user", "assistant") and content and content.strip():
            messages.append({"role": role, "content": content[:2000]})

    if len(messages) < 3:
        sys.exit(0)

    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = f"---\ndate: {today}\ntype: daily-log\n---\n\n# Daily Log — {today}\n\n"

    parts = [f"\n## Pre-compact save ({timestamp}, session {session_id[:8]})\n\n"]
    for msg in messages[-30:]:
        role = msg["role"].upper()
        content = msg["content"]
        # 1500 char truncation matches save_raw_log.py (was 500 — the
        # "insurance for long sessions" rationale was being undermined
        # by a tighter cap than the primary path).
        if len(content) > 1500:
            content = content[:1500] + "\n\n*[truncated]*"
        parts.append(f"**{role}:** {content}\n\n")
    parts.append("---\n")

    daily_log_write(vault_path, "".join(parts), header_if_new=header)
    sys.exit(0)


if __name__ == "__main__":
    main()
