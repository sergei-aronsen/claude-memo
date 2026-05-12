#!/usr/bin/env python3
"""
should_suggest_memo.py — Lightweight heuristic for Stop hook.

Reads the last few text-only messages from the transcript and checks if
they contain patterns that suggest a memo-worthy moment. If yes, injects
a system message nudging Claude to suggest /memo.

No API calls. No cost. Runs in <100ms.
"""

import json
import os
import sys
from collections import deque

# Signal categories. Decision/debug/pattern/tool are deliberately kept
# distinct so we can require hits in two DIFFERENT categories — that
# is a much higher-precision signal than "two of any 60+ words", which
# fires on routine debug chats and tool output (M-1 / N-H-I).
DECISION_SIGNALS = [
    "let's go with",
    "decided to use",
    "выбрали",
    "решили использовать",
    "tradeoff",
    "trade-off",
    "compromise",
    "instead of",
    "вместо",
    "better approach",
    "лучший подход",
    "the reason we",
    "chose",
    "picked",
    "switched to",
    "migrated to",
    "pros and cons",
    "плюсы и минусы",
]

DEBUG_SIGNALS = [
    "finally fixed",
    "the issue was",
    "root cause",
    "проблема была в",
    "turns out",
    "оказалось",
    "the bug was",
    "workaround",
    "after debugging",
    "took a while",
    "tricky",
    "нашли баг",
    "solution:",
    "fix:",
    "resolved by",
]

PATTERN_SIGNALS = [
    "pattern",
    "reusable",
    "паттерн",
    "можно переиспользовать",
    "boilerplate",
    "template",
    "шаблон",
    "helper",
    "utility",
    "abstraction",
    "wrapper",
]

TOOL_SIGNALS = [
    "discovered",
    "found this tool",
    "нашёл инструмент",
    "TIL",
    "til:",
    "useful command",
    "полезная команда",
    "config trick",
    "трюк с конфигом",
]

SIGNAL_CATEGORIES = {
    "decision": DECISION_SIGNALS,
    "debug": DEBUG_SIGNALS,
    "pattern": PATTERN_SIGNALS,
    "tool": TOOL_SIGNALS,
}

MIN_MESSAGES_FOR_SUGGESTION = 6  # Don't suggest on short sessions


def _extract_text_only_content(entry: dict) -> str:
    """Pull human-readable text from a Claude Code transcript entry.

    Skips tool_use and tool_result blocks entirely (N-H-I). A grep hit
    for the word "pattern" inside tool output was a guaranteed false
    positive that nagged users every Stop hook in any debug-heavy
    session.
    """
    # Handle nested format: {"type": "user", "message": {...}}
    if "message" in entry and isinstance(entry["message"], dict):
        entry = entry["message"]
    content = entry.get("content", "")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        # ONLY native "text" blocks. tool_use/tool_result are excluded so
        # tool output (grep results, file dumps) cannot trigger signals.
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Don't interfere if stop_hook_active (prevents loops)
    if hook_input.get("stop_hook_active"):
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    # N-M-12 / L-5: tail-read 64KB instead of readlines on the entire
    # transcript. Stop hook fires after EVERY assistant message — on a
    # 50MB transcript with hundreds of Stop fires per session the old
    # readlines pattern burned hundreds of MB of allocation per session.
    messages: list[str] = []
    try:
        with open(transcript_path, "rb") as fb:
            fb.seek(0, 2)
            size = fb.tell()
            fb.seek(max(0, size - 65536))
            tail = fb.read().decode("utf-8", errors="ignore")
    except OSError:
        sys.exit(0)

    # Use the last 20 lines of the tail (the first line may be partial —
    # safe to skip it with [1:] if the file is large enough that we
    # didn't read from offset 0).
    raw_lines = tail.splitlines()
    if size > 65536 and raw_lines:
        raw_lines = raw_lines[1:]
    for line in deque(raw_lines, maxlen=20):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        text = _extract_text_only_content(entry)
        if text:
            messages.append(text.lower())

    if len(messages) < MIN_MESSAGES_FOR_SUGGESTION:
        sys.exit(0)

    # Concatenate the last 5 messages and bucket-match signals.
    recent_text = " ".join(messages[-5:])
    categories_hit: set[str] = set()
    for cat, signals in SIGNAL_CATEGORIES.items():
        for s in signals:
            if s.lower() in recent_text:
                categories_hit.add(cat)
                break

    # M-1: require hits in TWO DIFFERENT categories. "decision + debug"
    # is interesting; "two debug words" was alert fatigue.
    if len(categories_hit) >= 2:
        output = {
            "systemMessage": (
                "This conversation contains knowledge worth saving "
                f"({', '.join(sorted(categories_hit))}). "
                "Consider suggesting the user run /memo to capture "
                "the key decision, pattern, or solution for future reference. "
                "Keep the suggestion brief and natural — one line at the end of your response."
            )
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
