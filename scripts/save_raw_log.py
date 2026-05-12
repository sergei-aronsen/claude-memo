#!/usr/bin/env python3
"""
save_raw_log.py — Stage 1 of the two-stage auto-memo pipeline.

Runs at SessionEnd. Fast, no API calls. Just saves the last 30 messages
from the transcript as a raw daily log in markdown format.

The compile step (compile_logs.py) runs later via cron and turns
these raw logs into structured wiki/memo articles.

Why two stages:
- SessionEnd has 1.5s timeout — can't do API calls reliably
- Even with nohup, keeping the fast path fast is better
- Raw logs capture EVERYTHING, compile can be selective
- If compile fails, raw logs are still there as backup
"""

import json
import os
import sys
from collections import deque
from datetime import datetime


def read_last_messages(transcript_path: str, max_messages: int = 30) -> list[dict]:
    """Read the last N messages from a JSONL transcript.

    Uses `collections.deque(maxlen=...)` so memory is O(maxlen) rather
    than O(file size). Long Claude Code transcripts routinely hit
    50-200 MB; the previous readlines() implementation materialized the
    whole file into a Python list before slicing, risking the 1.5s
    SessionEnd timeout on slow / Dropbox-backed disks.
    """
    messages = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            tail = deque(f, maxlen=max_messages * 3)

        for line in tail:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    continue
                # Handle Claude Code nested format: {"type": "user", "message": {"role": "user", "content": "..."}}
                if "message" in entry and isinstance(entry["message"], dict):
                    entry = entry["message"]
                role = entry.get("role", "")
                content = entry.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                    )
                if role in ("user", "assistant") and content and content.strip():
                    messages.append({"role": role, "content": content})
            except json.JSONDecodeError:
                continue
    except (OSError, UnicodeDecodeError):
        return []
    return messages[-max_messages:]


def save_daily_log(messages: list[dict], vault_path: str, session_id: str) -> str | None:
    """Append messages to today's daily log under fcntl.LOCK_EX."""
    sys.path.insert(0, os.path.dirname(__file__))
    from memo_utils import daily_log_write

    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = f"---\ndate: {today}\ntype: daily-log\n---\n\n# Daily Log — {today}\n\n"

    entry_parts = [f"\n## Session {session_id[:8]} ({timestamp})\n\n"]
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        # Truncate very long messages but keep enough for context
        if len(content) > 1500:
            content = content[:1500] + "\n\n*[truncated]*"
        entry_parts.append(f"**{role}:** {content}\n\n")
    entry_parts.append("---\n")

    return daily_log_write(vault_path, "".join(entry_parts), header_if_new=header)


def main():
    # Add scripts dir to path for memo_utils import
    sys.path.insert(0, os.path.dirname(__file__))
    from memo_utils import memo_log, resolve_vault_path

    vault_path = resolve_vault_path(sys.argv)

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    session_id = hook_input.get("session_id", "unknown")

    # Defense-in-depth: the hook (auto_memo_hook.sh) already gates on transcript
    # existence and size >= 2048 bytes. Silently exit here too in case save_raw_log.py
    # is invoked directly with an empty/header-only transcript (e.g., subagent SessionEnd).
    # Threshold matches the hook — see auto_memo_hook.sh for rationale. If the threshold
    # ever changes, both files must be updated in the same commit.
    _MIN_TRANSCRIPT_BYTES = 2048
    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)
    try:
        if os.path.getsize(transcript_path) < _MIN_TRANSCRIPT_BYTES:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    messages = read_last_messages(transcript_path)
    if len(messages) < 4:
        sys.exit(0)

    log_file = save_daily_log(messages, vault_path, session_id)

    if log_file:
        memo_log(
            vault_path,
            f"Raw log saved: {os.path.basename(log_file)} ({len(messages)} messages)",
            "raw-log",
        )


if __name__ == "__main__":
    main()
