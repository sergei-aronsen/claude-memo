#!/usr/bin/env python3
"""
memo_utils.py — Shared utilities for the Memo skill.

Single source of truth for:
- YAML frontmatter parsing (PyYAML, not hand-rolled)
- Anthropic API client (urllib, no curl, no API key in ps)
- save_memo() — writing structured notes to vault
- Logging
- Constants
"""

import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime

# Try PyYAML first (preferred), fall back to basic parser
try:
    import yaml  # PyYAML stubs optional; pyproject sets ignore_missing_imports

    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


# ─── Per-vault cache directory ───
#
# Architectural Tier 3: the per-machine cache (SQLite index, embeddings,
# logs, lock files, temp scratch) lives OUTSIDE the vault — in
# `~/.cache/memo/<hash>/` keyed by sha256(realpath(vault)). The vault
# itself only contains markdown (the actual knowledge) and a `.obsidian/`
# app config — both of which DO belong in Dropbox sync.
#
# Why moved:
#   - SQLite WAL sidecar files (.db-wal, .db-shm) are sync-hostile;
#     Dropbox saw them mid-write and produced "Conflicted Copy" files
#     that corrupted the database.
#   - Two machines writing to the same `.memo/` over Dropbox raced past
#     `fcntl.flock` (which is per-host) — no atomicity guarantee across
#     hosts.
#   - Logs grew unbounded inside a synced folder, wasting bandwidth.
#   - `auto_memo.log` and `hook_payloads.jsonl` could carry session paths
#     and tool inputs that should never leave the machine.
#
# Rebuilding the cache on a new machine takes one command:
#   python3 scripts/memo_engine.py reindex --full --vault <path>
# The vault itself is the source of truth.

_LEGACY_MEMO_DIRNAME = ".memo"


def _vault_hash(vault_path: str) -> str:
    """Stable per-machine hash of the resolved vault path (16 hex chars)."""
    real = os.path.realpath(vault_path)
    return hashlib.sha256(real.encode("utf-8")).hexdigest()[:16]


def get_memo_dir(vault_path: str) -> str:
    """Return the per-vault cache directory (auto-creates + auto-migrates).

    Path: ~/.cache/memo/<vault-hash>/

    On first call for a given vault, if the legacy `<vault>/.memo/`
    exists with contents and the cache dir is empty, the contents are
    moved to the cache and a breadcrumb file is left in the vault
    so future runs know the migration happened.
    """
    cache_root = os.path.expanduser("~/.cache/memo")
    cache_dir = os.path.join(cache_root, _vault_hash(vault_path))

    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        try:
            os.chmod(cache_dir, 0o700)
        except OSError:
            pass

    _maybe_migrate_legacy_memo_dir(vault_path, cache_dir)

    return cache_dir


def _maybe_migrate_legacy_memo_dir(vault_path: str, cache_dir: str) -> None:
    """One-shot migration: move contents of <vault>/.memo/ to cache_dir.

    Idempotent. Only fires when:
      - <vault>/.memo/ exists and has contents
      - cache_dir is empty or only has files migration would produce
      - no `.migrated-to-cache` breadcrumb exists in vault
    """
    legacy = os.path.join(vault_path, _LEGACY_MEMO_DIRNAME)
    breadcrumb = os.path.join(vault_path, _LEGACY_MEMO_DIRNAME + ".migrated-to-cache")

    if os.path.exists(breadcrumb):
        return
    if not os.path.isdir(legacy):
        return
    try:
        legacy_contents = os.listdir(legacy)
    except OSError:
        return
    if not legacy_contents:
        return

    cache_existing = set(os.listdir(cache_dir)) if os.path.isdir(cache_dir) else set()
    # If the cache already has a real db, don't blindly overwrite — bail
    # and let the user decide. (Defensive: should only happen if user
    # manually populated both.)
    if any(name in cache_existing for name in ("index.db", "embeddings.npy", "id_map.json")):
        return

    import sys

    print(
        f"[memo] migrating {legacy} → {cache_dir} (one-time architectural move)",
        file=sys.stderr,
    )

    for name in legacy_contents:
        src = os.path.join(legacy, name)
        dst = os.path.join(cache_dir, name)
        try:
            if os.path.isdir(src):
                # Merge directories rather than replace
                if os.path.isdir(dst):
                    for sub in os.listdir(src):
                        try:
                            shutil.move(os.path.join(src, sub), os.path.join(dst, sub))
                        except (OSError, shutil.Error):
                            pass
                    try:
                        os.rmdir(src)
                    except OSError:
                        pass
                else:
                    shutil.move(src, dst)
            else:
                shutil.move(src, dst)
        except (OSError, shutil.Error) as e:
            print(f"[memo] migrate skip {src}: {e}", file=sys.stderr)

    # Leave breadcrumb so we don't try again, and so user knows what
    # happened if they look in their vault.
    try:
        with open(breadcrumb, "w", encoding="utf-8") as f:
            f.write(
                "This vault used to have a `.memo/` directory inside it.\n"
                f"Contents have been moved to: {cache_dir}\n"
                "This file is a breadcrumb so the migration is not repeated.\n"
                "Safe to delete this file once you have confirmed the cache works.\n"
            )
    except OSError:
        pass

    # If legacy dir is now empty, remove it. Don't force-remove if any
    # files were left behind by a failed move.
    try:
        if not os.listdir(legacy):
            os.rmdir(legacy)
    except OSError:
        pass


# ─── YAML Frontmatter ───


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content.

    Uses PyYAML when available (handles colons in values, quotes,
    multiline, nested structures). Falls back to basic parser if
    PyYAML is not installed.

    Returns (metadata_dict, body_text).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    raw_yaml = parts[1].strip()
    body = parts[2].strip()

    if HAS_PYYAML:
        try:
            meta = yaml.safe_load(raw_yaml)
            if not isinstance(meta, dict):
                meta = {}
            return meta, body
        except yaml.YAMLError:
            return {}, content
    else:
        # Basic fallback (no PyYAML) — handles simple key: value and lists
        return _parse_frontmatter_basic(raw_yaml), body


def _parse_frontmatter_basic(raw_yaml: str) -> dict:
    """Fallback YAML parser for environments without PyYAML."""
    meta: dict[str, str | list[str]] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in raw_yaml.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip().strip("'\""))
            meta[current_key] = current_list
            continue

        if ":" in stripped:
            if current_list is not None:
                current_list = None

            # Use first colon only — handles "title: PostgreSQL: when to use jsonb"
            idx = stripped.index(":")
            key = stripped[:idx].strip()
            value = stripped[idx + 1 :].strip().strip("'\"")
            current_key = key

            if value:
                meta[key] = value
            else:
                current_list = []
                meta[key] = current_list

    return meta


def _yaml_needs_quoting(value: str) -> bool:
    """Check if a YAML string value needs quoting."""
    special_chars = (":", "#", "[", "]", "{", "}", "'", '"', "|", ">", "&", "*", "!", "%", "@", "`")
    return any(c in value for c in special_chars) or value.startswith(("-", "?", " ")) or "\n" in value


def build_frontmatter(meta: dict) -> str:
    """Build YAML frontmatter string from dict."""
    if HAS_PYYAML:
        import yaml

        yaml_str = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip()
        return f"---\n{yaml_str}\n---"

    # Fallback without PyYAML — quote all potentially unsafe values
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                item_str = str(item)
                if _yaml_needs_quoting(item_str):
                    item_str = '"' + item_str.replace("\\", "\\\\").replace('"', '\\"') + '"'
                lines.append(f"  - {item_str}")
        else:
            str_value = str(value)
            if isinstance(value, str) and _yaml_needs_quoting(str_value):
                str_value = '"' + str_value.replace("\\", "\\\\").replace('"', '\\"') + '"'
            lines.append(f"{key}: {str_value}")
    lines.append("---")
    return "\n".join(lines)


# ─── LLM API Client (configurable provider) ───

# Configuration via environment variables:
#   MEMO_API_PROVIDER  — "openrouter" (default) or "anthropic"
#   MEMO_MODEL         — model ID (default: provider-dependent)
#   MEMO_API_KEY       — API key (falls back to OPENROUTER_API_KEY or ANTHROPIC_API_KEY)
#   MEMO_API_URL       — override API endpoint URL
#
# Defaults:
#   OpenRouter: google/gemini-2.5-flash via https://openrouter.ai/api/v1/chat/completions
#   Anthropic:  claude-haiku-4-5-20251001 via https://api.anthropic.com/v1/messages

PROVIDER_DEFAULTS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "google/gemini-2.5-flash-lite",
        "fallback_model": "google/gemini-3-flash-preview",
        "key_env": "OPENROUTER_API_KEY",
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-haiku-4-5-20251001",
        "fallback_model": "claude-sonnet-4-6-20250514",
        "key_env": "ANTHROPIC_API_KEY",
    },
}

# Allowed URL prefixes for API endpoints (SSRF protection)
ALLOWED_API_URL_PREFIXES = (
    "https://api.anthropic.com/",
    "https://openrouter.ai/",
    "https://api.openai.com/",
)


def _get_provider_config() -> dict:
    """Resolve provider, model, key, and URL from environment."""
    provider = os.environ.get("MEMO_API_PROVIDER", "").lower()

    # Auto-detect provider from available keys if not explicitly set
    if not provider:
        if os.environ.get("OPENROUTER_API_KEY"):
            provider = "openrouter"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "openrouter"

    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["openrouter"])

    api_key = os.environ.get("MEMO_API_KEY") or os.environ.get(defaults["key_env"]) or ""
    model = os.environ.get("MEMO_MODEL") or defaults["model"]
    fallback = os.environ.get("MEMO_FALLBACK_MODEL") or defaults["fallback_model"]
    url = os.environ.get("MEMO_API_URL") or defaults["url"]

    # Validate URL against allowlist (SSRF protection)
    if not any(url.startswith(prefix) for prefix in ALLOWED_API_URL_PREFIXES):
        raise ValueError(
            f"MEMO_API_URL '{url}' is not in the allowed list. Allowed prefixes: {', '.join(ALLOWED_API_URL_PREFIXES)}"
        )

    return {
        "provider": provider,
        "url": url,
        "model": model,
        "fallback_model": fallback,
        "api_key": api_key,
    }


def call_llm(prompt: str, max_tokens: int = 4000, system: str | None = None) -> str | None:
    """Call LLM via configurable provider with automatic fallback.

    Tries the primary model first. If it fails (timeout, error, empty
    response), automatically retries with the fallback model.

    Returns the text response, or None if both models fail.
    """
    config = _get_provider_config()
    api_key = config["api_key"]

    if not api_key:
        return None

    # Try primary model. Distinguish None (transport / parse failure —
    # retry on fallback) from "" (legitimate empty completion — return
    # directly, don't double-bill). The old `if result:` truthiness
    # check retried on every empty string, doubling Haiku spend on
    # any "no memo-worthy content" session.
    result = _call_model(prompt, max_tokens, system, config, config["model"])
    if result is not None:
        return result

    # Primary failed — try fallback
    fallback = config.get("fallback_model")
    if fallback and fallback != config["model"]:
        result = _call_model(prompt, max_tokens, system, config, fallback)
        if result is not None:
            return result

    return None


def _call_model(prompt: str, max_tokens: int, system: str | None, config: dict[str, str], model: str) -> str | None:
    """Call a specific model. Returns text or None on failure."""
    cfg = {**config, "model": model}
    if config["provider"] == "anthropic":
        return _call_anthropic(prompt, max_tokens, system, cfg)
    else:
        return _call_openai_compat(prompt, max_tokens, system, cfg)


# User-Agent for outgoing HTTP. Per the global security rules, the
# default `Python-urllib/3.x` UA is a known fingerprint that some
# providers and corporate proxies block or rate-limit. A clearly-
# identified tool UA is the standard for API clients.
_USER_AGENT = "claude-memo/1.0 (+https://github.com/sergei-aronsen/claude-memo)"


def _call_anthropic(prompt: str, max_tokens: int, system: str | None, config: dict[str, str]) -> str | None:
    """Call Anthropic API (Messages format). Returns the text on success
    (possibly empty string for legitimate "nothing to say" completions),
    or None on transport/auth/parse failure.
    """
    if not config["url"].startswith("https://"):
        import sys

        print(f"[memo] refusing non-https API URL: {config['url']!r}", file=sys.stderr)
        return None

    body = {
        "model": config["model"],
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    req = urllib.request.Request(
        config["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": config["api_key"],
            "anthropic-version": "2023-06-01",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310 — https scheme allowlisted above
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        import sys

        print(f"[memo] Anthropic API call failed: {e}", file=sys.stderr)
        return None

    content = result.get("content", [])
    if isinstance(content, list) and len(content) > 0:
        return content[0].get("text", "")
    return ""  # API succeeded but had no content blocks — legitimate empty, not failure


def _call_openai_compat(prompt: str, max_tokens: int, system: str | None, config: dict[str, str]) -> str | None:
    """Call OpenAI-compatible API (OpenRouter, OpenAI, etc.).
    Returns text on success (possibly empty), None on transport failure.
    """
    if not config["url"].startswith("https://"):
        import sys

        print(f"[memo] refusing non-https API URL: {config['url']!r}", file=sys.stderr)
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": config["model"],
        "max_tokens": max_tokens,
        "messages": messages,
    }

    req = urllib.request.Request(
        config["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310 — https scheme allowlisted above
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        import sys

        print(f"[memo] OpenAI-compat API call failed: {e}", file=sys.stderr)
        return None

    choices = result.get("choices", [])
    if choices and len(choices) > 0:
        return choices[0].get("message", {}).get("content", "")
    return ""


# Backward-compatible alias
def call_haiku(prompt: str, max_tokens: int = 4000, system: str | None = None) -> str | None:
    """Backward-compatible alias for call_llm."""
    return call_llm(prompt, max_tokens, system)


def parse_json_response(text: str) -> list | dict | None:
    """Parse JSON from LLM response, stripping markdown fences."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ─── Save Memo (single source of truth) ───


def save_memo(
    memo: dict,
    vault_path: str,
    session_id: str = "manual",
    source: str = "auto-memo",
) -> str | None:
    """Save a structured memo to the vault. Used by auto_memo and compile_logs.

    Args:
        memo: Dict with keys: type, title, project, tags, aliases,
              context, content, alternatives, consequences, related
        vault_path: Path to vault root
        session_id: Session identifier for frontmatter
        source: Source tag (auto-memo, auto-compile, manual)

    Returns filepath of saved note, or None on failure.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    memo_type = memo.get("type", "insight")
    title = memo.get("title", "Untitled")

    # Generate slug
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s]+", "-", slug)
    slug = slug[:80]

    # Type → folder mapping
    type_folders = {
        "decision": "decisions",
        "pattern": "patterns",
        "debug": "debug-logs",
        "insight": "insights",
        "tool": "tools",
    }
    folder = type_folders.get(memo_type, "insights")
    folder_path = os.path.join(vault_path, folder)
    os.makedirs(folder_path, exist_ok=True)

    # Unique filename — open with O_CREAT|O_EXCL atomically so two
    # concurrent SessionEnd hooks on the same topic at the same second
    # cannot both observe a missing file and then race to open(..., "w").
    # The previous `while os.path.exists` + later open() was TOCTOU:
    # both writers passed the check, both wrote, second overwrote first.
    filename = f"{today}-{slug}.md"
    filepath = os.path.join(folder_path, filename)
    counter = 1
    fd: int | None = None
    while True:
        try:
            fd = os.open(filepath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            break
        except FileExistsError:
            filepath = os.path.join(folder_path, f"{today}-{slug}-{counter}.md")
            counter += 1
            if counter > 1000:
                # Defensive: should never happen but bail rather than spin
                memo_log(vault_path, f"save_memo: counter exhausted for slug={slug}", "error")
                return None

    # Build frontmatter
    tags = memo.get("tags", [])
    aliases = memo.get("aliases", [])
    project = memo.get("project")

    # Derive the memory tier (working/episodic/semantic/procedural) from
    # the note type. Stored in frontmatter so retention/decay policies can
    # treat episodic and semantic notes differently without re-parsing
    # the type field across the vault. Memo dict can override via "tier".
    from memo_engine import derive_tier

    tier = memo.get("tier") or derive_tier(memo_type)

    fm_dict = {
        "type": memo_type,
        "tier": tier,
        "created": today,
        "updated": today,
        "source": source,
    }
    if session_id != "manual":
        fm_dict["session"] = session_id[:12]
    if project:
        fm_dict["project"] = project
    if tags:
        fm_dict["tags"] = tags
    if aliases:
        fm_dict["aliases"] = aliases

    # Build body
    header_map = {
        "decision": "Decision",
        "pattern": "Pattern",
        "debug": "Solution",
        "insight": "Insight",
        "tool": "Tool",
    }

    sections = [build_frontmatter(fm_dict), f"\n# {title}\n"]

    if memo.get("context"):
        sections.append(f"## Context\n\n{memo['context']}\n")

    if memo.get("content"):
        header = header_map.get(memo_type, "Content")
        sections.append(f"## {header}\n\n{memo['content']}\n")

    if memo.get("alternatives") and memo_type == "decision":
        sections.append(f"## Alternatives Considered\n\n{memo['alternatives']}\n")

    if memo.get("consequences"):
        sections.append(f"## Consequences\n\n{memo['consequences']}\n")

    # Provenance: backlink to the daily-log + session that produced the
    # note. Lets a future reader jump from a distilled note back to the
    # raw conversation. Skipped for manually-created notes.
    if session_id != "manual":
        source_lines = [
            f"- Session: `{session_id[:12]}`",
            f"- Daily log: [[daily-logs/{today}]]",
            f"- Source: {source}",
        ]
        sections.append("## Source\n\n" + "\n".join(source_lines) + "\n")

    # Related links
    related = memo.get("related", [])
    if related:
        sections.append("## Related\n\n" + "\n".join(f"- [[{r}]]" for r in related) + "\n")
    else:
        sections.append("## Related\n\n*(auto-generated, review and add links)*\n")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = None  # ownership transferred to fdopen
            f.write("\n".join(sections))

        # Append to INDEX.md (with month header for rotation)
        append_to_index(vault_path, filepath, title, source)

        return filepath
    except OSError as e:
        memo_log(vault_path, f"save_memo failed: {e}", "error")
        # If the file was created but the write failed, attempt to remove
        # it so a retry doesn't trip the O_EXCL guard on the next call.
        try:
            os.remove(filepath)
        except OSError:
            pass
        return None
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def append_to_index(vault_path: str, filepath: str, title: str, source: str):
    """Append entry to INDEX.md with monthly sections.

    Acquires fcntl.LOCK_EX on the index file so concurrent SessionEnd /
    auto-compile writers cannot interleave bytes mid-line or both insert
    the same monthly header.
    """
    import fcntl

    index_path = os.path.join(vault_path, "INDEX.md")
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    rel = os.path.relpath(filepath, vault_path)
    link = os.path.splitext(rel)[0]

    month_header = f"\n## {month}\n"
    entry = f"- [{today}] [[{link}]] — {title} *({source})*\n"

    try:
        # Open in r+/a hybrid: create if missing, take exclusive lock,
        # then read full content under the lock to decide whether to
        # emit the month header.
        fd = os.open(index_path, os.O_RDWR | os.O_CREAT, 0o644)
        ownership_transferred = False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as f:
                existing = f.read()
                # Pointer is at EOF after read — append directly.
                if month_header.strip() not in existing:
                    f.write(month_header)
                f.write(entry)
                ownership_transferred = True  # fdopen now owns fd; do not double-close
        finally:
            if not ownership_transferred:
                try:
                    os.close(fd)
                except OSError:
                    pass
    except OSError as e:
        memo_log(vault_path, f"append_to_index failed: {e}", "error")


# ─── Vault path resolution ───


def resolve_vault_path(argv: list[str] | None = None) -> str:
    """Resolve vault path from env, CLI args, or default.

    Priority: MEMO_VAULT_PATH env > --vault CLI arg > ~/memo-vault default.
    Exits with error if no vault found.
    """
    vault_path = os.path.expanduser(os.environ.get("MEMO_VAULT_PATH", ""))

    if not vault_path and argv:
        for i, arg in enumerate(argv):
            if arg == "--vault" and i + 1 < len(argv):
                vault_path = os.path.expanduser(argv[i + 1])

    if not vault_path:
        default = os.path.expanduser("~/memo-vault")
        if os.path.exists(default):
            vault_path = default
        else:
            import sys

            print(
                "Error: MEMO_VAULT_PATH is not set and ~/memo-vault does not exist.\n"
                "Set the environment variable: export MEMO_VAULT_PATH=/path/to/your/vault\n"
                "Or pass --vault /path/to/your/vault",
                file=sys.stderr,
            )
            sys.exit(1)

    return vault_path


# ─── Daily-log write (shared by save_raw_log, pre_compact_save, auto_memo, compile_logs) ───


def daily_log_write(vault_path: str, body: str, header_if_new: str | None = None) -> str | None:
    """Append `body` to today's daily-logs/YYYY-MM-DD.md under fcntl.LOCK_EX.

    If the file does not exist yet and `header_if_new` is provided, the
    header is emitted first so the file always opens with frontmatter.

    The whole write happens under a single LOCK_EX so multi-window
    SessionEnd / PreCompact hooks cannot interleave bytes within or
    across lines. Returns the log file path on success, or None on
    OSError (caller already logs / ignores).
    """
    import fcntl

    logs_dir = os.path.join(vault_path, "daily-logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except OSError:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"{today}.md")

    try:
        fd = os.open(log_file, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o644)
    except OSError:
        return None

    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            # We need to know whether the file is empty BEFORE appending,
            # so the header is only emitted once even under contention.
            file_was_empty = os.fstat(fd).st_size == 0
            with os.fdopen(fd, "a", encoding="utf-8", closefd=True) as f:
                fd_owned = False  # ownership transferred to fdopen
                if file_was_empty and header_if_new:
                    f.write(header_if_new)
                f.write(body)
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            # If fdopen() already closed the fd, the flock unlock above
            # may have failed silently; that's fine. The os.close in this
            # branch only fires when fdopen never ran (e.g. raise before).
            if "fd_owned" not in dir() or fd_owned:
                try:
                    os.close(fd)
                except OSError:
                    pass
    except OSError:
        return None

    return log_file


# ─── Logging ───


def memo_log(vault_path: str, message: str, component: str = "memo"):
    """Append timestamped message to <cache>/auto_memo.log."""
    import fcntl

    log_path = os.path.join(get_memo_dir(vault_path), "auto_memo.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{component}] {message}\n"
    try:
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    except OSError:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def index_memo_file(filepath: str, vault_path: str):
    """Index a memo file in the search engine (direct call, no subprocess).

    Used for retroactive indexing only — new writes should go through
    save_memo_and_index() so the file-on-disk and SQLite row appear
    under one lock.
    """
    try:
        import sys

        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        from memo_engine import EmbeddingsStore, VaultLock, index_file, init_db

        with VaultLock(vault_path):
            conn = init_db(vault_path)
            store = EmbeddingsStore(vault_path)
            try:
                index_file(filepath, vault_path, conn, store)
            finally:
                conn.close()
    except Exception as e:
        memo_log(vault_path, f"index_memo_file failed for {filepath}: {e}", "error")


def save_memo_and_index(
    memo: dict,
    vault_path: str,
    session_id: str = "manual",
    source: str = "auto-memo",
) -> str | None:
    """Atomically save a memo and index it under a single VaultLock.

    H-CONC-4: the previous pattern was `filepath = save_memo(...)` followed
    by `index_memo_file(filepath, ...)`. Between those two calls the file
    existed on disk but had no SQLite row — a reader scanning the
    filesystem could miss the note in search results. This wrapper takes
    VaultLock once, performs both writes, and releases. From a reader's
    perspective the note appears in both stores atomically with respect
    to other writers.

    Returns filepath of saved note, or None on save failure. Indexing
    failures are logged but do not unlink the note (the cron reindex
    will pick it up on next pass).
    """
    import sys

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from memo_engine import EmbeddingsStore, VaultLock, detect_supersede, index_file, init_db

    with VaultLock(vault_path):
        filepath = save_memo(memo, vault_path, session_id=session_id, source=source)
        if not filepath:
            return None
        try:
            conn = init_db(vault_path)
            store = EmbeddingsStore(vault_path)
            try:
                note_id = index_file(filepath, vault_path, conn, store)
                # F3: auto-supersede older contradicting notes (opt-out via
                # MEMO_AUTO_SUPERSEDE=0). Conservative — only fires on a
                # high-confidence opposite-polarity match against an older note.
                if note_id is not None and os.environ.get("MEMO_AUTO_SUPERSEDE", "1") != "0":
                    superseded = detect_supersede(note_id, vault_path, conn, store)
                    if superseded:
                        memo_log(
                            vault_path,
                            f"auto-superseded {len(superseded)} note(s) by '{memo.get('title')}': {superseded}",
                            "info",
                        )
            finally:
                conn.close()
        except Exception as e:
            memo_log(
                vault_path,
                f"save_memo_and_index: indexing failed for {filepath}: {e}",
                "error",
            )
        return filepath
