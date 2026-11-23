"""
privacy.py — Secret/PII redaction before persistence and before LLM calls.

Used to keep credentials, tokens, and personal paths out of:
  1. The conversation sent to the classifier LLM (data leaving the machine)
  2. The notes written to the Obsidian vault (data shared via git / sync)

Design notes:
  - Patterns are conservative. False positives (a legitimate value
    accidentally redacted) are recoverable from the daily-log; false
    negatives (a real secret committed to the vault) are not.
  - Returns the redacted text *and* a list of labels so callers can log
    "stripped 2 api_key + 1 home_path" without revealing the secret.
  - No regex captures the secret in a way that ends up in the return
    value of any caller — labels are fixed strings.
"""

from __future__ import annotations

import re
from typing import Pattern

_PATTERNS: list[tuple[str, Pattern[str]]] = [
    # Order matters: more-specific patterns before generic ones.
    # Anthropic API keys
    ("api_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{40,}")),
    # OpenAI-style keys (sk-..., 32+ alnum)
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    # GitHub PAT / OAuth / app tokens
    ("api_key", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("api_key", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82,}\b")),
    # Slack tokens
    ("api_key", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    # AWS access key ID
    ("api_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # Google API keys
    ("api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    # Generic JWTs (3 base64url segments separated by dots, starting eyJ)
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    # Bearer authorization headers
    ("bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    # PEM private keys (multiline)
    (
        "private_key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
    ),
    # password = "..." / password: "..." (quoted value of >=4 chars)
    (
        "password",
        re.compile(
            r"""(?i)\b(?:password|passwd|pwd|secret)\s*[:=]\s*["']([^"'\n]{4,})["']""",
        ),
    ),
]

# Home paths get rewritten rather than fully redacted because they're
# common in command output and stripping them entirely makes notes useless.
_HOME_PATTERNS: list[tuple[Pattern[str], str]] = [
    (re.compile(r"/Users/[^/\s\"']+"), "/Users/<user>"),
    (re.compile(r"/home/[^/\s\"']+"), "/home/<user>"),
    (re.compile(r"C:\\Users\\[^\\\s\"']+", re.IGNORECASE), r"C:\\Users\\<user>"),
]

# Personal-looking email addresses. Allowlist common impersonal addresses
# (noreply, support, info, abuse, admin, ...) so docs that mention them
# stay intact.
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_EMAIL_ALLOWLIST_LOCAL = {
    "noreply",
    "no-reply",
    "support",
    "info",
    "admin",
    "abuse",
    "security",
    "hello",
    "contact",
    "help",
    "team",
    "example",
}


def _redact_email(match: re.Match[str]) -> str:
    addr = match.group(0)
    local = addr.split("@", 1)[0].lower()
    if local in _EMAIL_ALLOWLIST_LOCAL:
        return addr
    return "[REDACTED:email]"


def strip_secrets(text: str) -> tuple[str, list[str]]:
    """Redact secrets and personal data from `text`.

    Returns (sanitized_text, redaction_labels). `redaction_labels` is a
    multiset (list) of labels — one entry per redacted span — so callers
    can report counts without exposing the original values.
    """
    if not text:
        return text, []

    labels: list[str] = []
    out = text

    for label, pattern in _PATTERNS:

        def _sub(_m: re.Match[str], _label: str = label) -> str:
            labels.append(_label)
            return f"[REDACTED:{_label}]"

        out = pattern.sub(_sub, out)

    for pattern, replacement in _HOME_PATTERNS:

        def _sub_home(m: re.Match[str], _repl: str = replacement) -> str:
            # Only flag redactions where the username is non-trivial.
            # "/Users/<user>" → "/Users/<user>" is a no-op, don't count it.
            if m.group(0) != _repl:
                labels.append("home_path")
            return _repl

        out = pattern.sub(_sub_home, out)

    def _email_sub(m: re.Match[str]) -> str:
        result = _redact_email(m)
        if result != m.group(0):
            labels.append("email")
        return result

    out = _EMAIL_RE.sub(_email_sub, out)

    return out, labels


def summarize_redactions(labels: list[str]) -> str:
    """Compact summary like 'api_key=2, home_path=1' for log lines."""
    if not labels:
        return ""
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
