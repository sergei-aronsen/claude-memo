#!/usr/bin/env python3
"""
auto_memo.py — Automatic memo extraction from Claude Code session transcripts.

Runs as a SessionEnd hook. Reads the session transcript, detects memo-worthy
content (decisions, patterns, debug solutions, insights), and auto-saves
notes to the Obsidian vault.

Usage (called by Claude Code hook, not manually):
  echo '{"transcript_path": "...", "session_id": "..."}' | python auto_memo.py --vault ~/memo-vault

How it works:
  1. Reads the JSONL transcript file
  2. Extracts assistant + user messages
  3. Sends to Claude API (Haiku — fast and cheap) with a classification prompt
  4. If memo-worthy content found → generates structured notes
  5. Saves to vault, indexes in SQLite + embeddings
  6. Logs what was saved for transparency

Cost: ~$0.001-0.005 per session (Haiku). Runs async, doesn't block.
"""

import argparse
import json
import os
import sys
from datetime import datetime


def _extract_entry_message(entry: dict) -> tuple[str, str]:
    """Pull (role, content) from a single transcript entry."""
    # Handle Claude Code nested format: {"type": "user", "message": {...}}
    if "message" in entry and isinstance(entry["message"], dict):
        entry = entry["message"]

    role = entry.get("role", "")
    content = entry.get("content", "")

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "text":
                text_parts.append(block.get("text", ""))
            elif btype == "tool_use":
                tool_name = block.get("name", "unknown_tool")
                tool_input = json.dumps(block.get("input", {}))[:200]
                text_parts.append(f"[Used tool: {tool_name}({tool_input})]")
            elif btype == "tool_result":
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    result_content = " ".join(b.get("text", "") for b in result_content if isinstance(b, dict))
                if result_content:
                    text_parts.append(f"[Tool result: {str(result_content)[:200]}]")
        content = "\n".join(text_parts)
    elif isinstance(content, str):
        pass
    else:
        content = str(content)[:500] if content else ""

    return role, content


def read_transcript(transcript_path: str, vault_path: str | None = None) -> list[dict]:
    """Read JSONL transcript and extract conversation messages.

    Robust to:
    - Standard JSONL ({role, content} per line)
    - Multi-line pretty-printed JSON (single top-level object/array)
    - Mid-line truncation (last partial line)
    - Format changes (logged once, not silently swallowed)
    """
    messages: list[dict] = []
    decode_failures = 0
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    decode_failures += 1
                    if decode_failures > 3 and not messages:
                        # Likely not JSONL after all. Bail out of the
                        # line-by-line loop and try whole-file parse below.
                        break
                    continue

                if not isinstance(entry, dict):
                    continue
                role, content = _extract_entry_message(entry)
                if role in ("user", "assistant") and content and content.strip():
                    messages.append({"role": role, "content": content})
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return []
    except (OSError, UnicodeDecodeError) as e:
        if vault_path:
            from memo_utils import memo_log

            memo_log(vault_path, f"read_transcript I/O error: {e}", "auto-memo")
        return messages

    if messages:
        return messages

    # N-H-M: Empty result + decode failures > 3 → likely pretty-printed JSON.
    # Try whole-file parse before giving up.
    if decode_failures > 0:
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            if vault_path:
                from memo_utils import memo_log

                memo_log(
                    vault_path,
                    f"read_transcript: unknown format (decode_failures={decode_failures})",
                    "auto-memo",
                )
            return []

        # Best-effort walk: top-level array → entries; top-level dict
        # with "messages"/"entries" key → entries.
        candidates: list = []
        if isinstance(obj, list):
            candidates = obj
        elif isinstance(obj, dict):
            for k in ("messages", "entries", "history"):
                if isinstance(obj.get(k), list):
                    candidates = obj[k]
                    break

        for entry in candidates:
            if isinstance(entry, dict):
                role, content = _extract_entry_message(entry)
                if role in ("user", "assistant") and content and content.strip():
                    messages.append({"role": role, "content": content})

    return messages


def truncate_conversation(messages: list[dict], max_chars: int = 15000) -> str:
    """Build a truncated conversation string for the classifier.

    M-6: iterates messages in REVERSE so the END of the session
    (where decisions, conclusions, and final commits live) is kept
    when the budget runs out. The previous implementation kept the
    START — for long sessions, that meant the classifier saw
    "please refactor" but never the resulting decisions.
    """
    parts: list[str] = []
    total = 0
    for msg in reversed(messages):
        role = msg["role"].upper()
        content = msg["content"]
        if len(content) > 2000:
            content = content[:2000] + "... [truncated]"
        line = f"[{role}]: {content}"
        if total + len(line) > max_chars:
            parts.append("... [earlier conversation truncated]")
            break
        parts.append(line)
        total += len(line)
    parts.reverse()
    return "\n\n".join(parts)


def classify_and_extract(conversation: str, vault_path: str) -> list[dict]:
    """
    Send conversation to Claude Haiku for classification and extraction.
    Returns list of memo dicts ready to save.
    """
    prompt = f"""Analyze this Claude Code session transcript.
Extract any knowledge worth saving for long-term engineering memory.

Look for:
1. **Decisions** — architecture choices, tech stack picks, tradeoffs discussed
2. **Patterns** — reusable code approaches, techniques established
3. **Debug solutions** — non-trivial bugs solved (took multiple attempts)
4. **Insights** — learnings, "aha" moments, performance discoveries
5. **Tool discoveries** — new CLI tools, configs, workflow improvements

Rules:
- Only extract genuinely useful knowledge. Skip casual chat, simple questions, trivial fixes.
- If nothing is memo-worthy, return an empty array.
- Be concise. Each memo should be a distilled atomic note, not a transcript dump.
- Write in the same language as the conversation (Russian or English).
- Keep technical terms in English regardless of language.

Return ONLY a JSON array (no markdown, no backticks). Each item:
{{
  "type": "decision|pattern|debug|insight|tool",
  "title": "Clear searchable title (like a search query you'd use in 6 months)",
  "project": "project name if identifiable, or null",
  "tags": ["tag1", "tag2"],
  "aliases": ["alternative name 1"],
  "context": "Why this came up, 2-3 sentences",
  "content": "The actual knowledge, specific and concrete",
  "alternatives": "What else was considered (for decisions), or null",
  "consequences": "What this means going forward, or null"
}}

If nothing is worth saving, return: []

TRANSCRIPT:
{conversation}"""

    # Use secure API client (no curl, no API key in ps)
    from memo_utils import call_llm, memo_log, parse_json_response

    text = call_llm(prompt, max_tokens=4000)
    if text is None:
        # H-ROB-2: distinguish API failure from "no memo-worthy content".
        # Previously both took the same code path and emitted the same log
        # line; if Haiku had been broken for a week the user would not
        # know. None now ONLY signals transport/auth/timeout failures.
        memo_log(
            vault_path,
            "[ERROR] API call failed — check OPENROUTER_API_KEY / ANTHROPIC_API_KEY and network",
            "auto-memo",
        )
        return []
    if not text.strip():
        memo_log(vault_path, "API returned empty response", "auto-memo")
        return []

    memos = parse_json_response(text)
    if not isinstance(memos, list):
        return []
    return memos


def _save_memo(memo: dict, vault_path: str, session_id: str) -> str | None:
    """Delegate to shared save_memo_and_index in memo_utils.

    Atomic save+index under one VaultLock so a reader never sees the
    note on disk without an SQLite row (H-CONC-4).
    """
    from memo_utils import save_memo_and_index

    return save_memo_and_index(memo, vault_path, session_id=session_id, source="auto-memo")


def _write_daily_log_marker(vault_path: str, marker: str) -> None:
    """Append a marker line to today's daily log via shared helper.

    Marker is best-effort: if the file does not yet exist there's
    nothing to claim (Stage 1 would create it just before Stage 2
    runs detached, but if Stage 1 was skipped we silently no-op).
    """
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = os.path.join(vault_path, "daily-logs", f"{today}.md")
    if not os.path.exists(daily_log):
        return
    from memo_utils import daily_log_write

    daily_log_write(vault_path, marker)


def main():
    from memo_utils import memo_log

    parser = argparse.ArgumentParser(description="Auto-memo from Claude Code transcript")
    parser.add_argument("--vault", required=True, help="Path to vault root")
    args = parser.parse_args()
    vault_path = os.path.expanduser(args.vault)

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        memo_log(vault_path, "No valid JSON on stdin", "auto-memo")
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    session_id = hook_input.get("session_id", "unknown")

    # Defense-in-depth: the hook (auto_memo_hook.sh) already gates on transcript
    # existence and size >= 2048 bytes. We silently exit here in case auto_memo.py
    # is invoked directly with a bad path. No log line — the hook owns gating telemetry.
    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    memo_log(vault_path, f"Processing session {session_id[:12]}...", "auto-memo")

    # 1. Read transcript
    messages = read_transcript(transcript_path, vault_path=vault_path)
    if len(messages) < 4:
        memo_log(vault_path, f"Session too short ({len(messages)} messages), skipping", "auto-memo")
        sys.exit(0)

    # 2. Claim the daily log BEFORE the Haiku call.
    # Closes the cron race: if SessionEnd happens at 17:59 and Haiku takes 30s,
    # cron at 18:00 must not re-process the same content. Cron treats both
    # `<!-- auto-processing` and `<!-- auto-processed` as already-claimed.
    started_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _write_daily_log_marker(
        vault_path,
        f"\n<!-- auto-processing session={session_id[:12]} started={started_at} -->\n",
    )

    # 3. Truncate and classify
    conversation = truncate_conversation(messages)
    memos = classify_and_extract(conversation, vault_path)

    saved: list[str] = []
    if memos:
        for memo in memos:
            filepath = _save_memo(memo, vault_path, session_id)
            if filepath:
                saved.append(filepath)

    # 4. Finalize the marker REGARDLESS of saved count.
    # Empty-memo sessions must still flip the marker, otherwise the
    # cron job at 18:00 will re-process them and double-bill Haiku
    # (which may then extract memos Stage 2 deemed unworthy — contradictory output).
    _write_daily_log_marker(
        vault_path,
        f"\n<!-- auto-processed session={session_id[:12]} memos={len(saved)} -->\n",
    )

    if not memos:
        memo_log(vault_path, "No memo-worthy content found", "auto-memo")
        sys.exit(0)

    saved_names = ", ".join(os.path.basename(f) for f in saved)
    memo_log(vault_path, f"Auto-saved {len(saved)} memo(s): {saved_names}", "auto-memo")


if __name__ == "__main__":
    main()
