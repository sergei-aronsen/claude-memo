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

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime

# Try PyYAML first (preferred), fall back to basic parser
try:
    import yaml  # type: ignore[import-untyped]  # stubs optional: pip install types-PyYAML

    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


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

    # Try primary model
    result = _call_model(prompt, max_tokens, system, config, config["model"])
    if result:
        return result

    # Primary failed — try fallback
    fallback = config.get("fallback_model")
    if fallback and fallback != config["model"]:
        result = _call_model(prompt, max_tokens, system, config, fallback)
        if result:
            return result

    return None


def _call_model(prompt: str, max_tokens: int, system: str | None, config: dict[str, str], model: str) -> str | None:
    """Call a specific model. Returns text or None on failure."""
    cfg = {**config, "model": model}
    if config["provider"] == "anthropic":
        return _call_anthropic(prompt, max_tokens, system, cfg)
    else:
        return _call_openai_compat(prompt, max_tokens, system, cfg)


def _call_anthropic(prompt: str, max_tokens: int, system: str | None, config: dict[str, str]) -> str | None:
    """Call Anthropic API (Messages format)."""
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
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
            return None
    except Exception as e:
        # Log to stderr for hook scripts; don't crash
        import sys

        print(f"[memo] Anthropic API call failed: {e}", file=sys.stderr)
        return None


def _call_openai_compat(prompt: str, max_tokens: int, system: str | None, config: dict[str, str]) -> str | None:
    """Call OpenAI-compatible API (OpenRouter, OpenAI, etc.)."""
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
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if choices and len(choices) > 0:
                return choices[0].get("message", {}).get("content", "")
            return None
    except Exception as e:
        import sys

        print(f"[memo] OpenAI-compat API call failed: {e}", file=sys.stderr)
        return None


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

    # Unique filename
    filename = f"{today}-{slug}.md"
    filepath = os.path.join(folder_path, filename)
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(folder_path, f"{today}-{slug}-{counter}.md")
        counter += 1

    # Build frontmatter
    tags = memo.get("tags", [])
    aliases = memo.get("aliases", [])
    project = memo.get("project")

    fm_dict = {
        "type": memo_type,
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

    # Related links
    related = memo.get("related", [])
    if related:
        sections.append("## Related\n\n" + "\n".join(f"- [[{r}]]" for r in related) + "\n")
    else:
        sections.append("## Related\n\n*(auto-generated, review and add links)*\n")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        # Append to INDEX.md (with month header for rotation)
        append_to_index(vault_path, filepath, title, source)

        return filepath
    except Exception as e:
        memo_log(vault_path, f"save_memo failed: {e}", "error")
        return None


def append_to_index(vault_path: str, filepath: str, title: str, source: str):
    """Append entry to INDEX.md with monthly sections."""
    index_path = os.path.join(vault_path, "INDEX.md")
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    rel = os.path.relpath(filepath, vault_path)
    link = os.path.splitext(rel)[0]

    month_header = f"\n## {month}\n"
    entry = f"- [{today}] [[{link}]] — {title} *({source})*\n"

    # Check if month header exists, add if not
    try:
        existing = ""
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                existing = f.read()

        if month_header.strip() not in existing:
            with open(index_path, "a", encoding="utf-8") as f:
                f.write(month_header)

        with open(index_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        memo_log(vault_path, f"append_to_index failed: {e}", "error")


# ─── Vault path resolution ───


def resolve_vault_path(argv: list[str] | None = None) -> str:
    """Resolve vault path from env, CLI args, or default.

    Priority: MEMO_VAULT_PATH env > --vault CLI arg > ~/memo-vault default.
    Exits with error if no vault found.
    """
    vault_path = os.environ.get("MEMO_VAULT_PATH", "")

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


# ─── Logging ───


def memo_log(vault_path: str, message: str, component: str = "memo"):
    """Append timestamped message to .memo/auto_memo.log."""
    log_path = os.path.join(vault_path, ".memo", "auto_memo.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{component}] {message}\n")
    except Exception:
        pass  # Cannot log a logging failure — silently ignore


def index_memo_file(filepath: str, vault_path: str):
    """Index a memo file in the search engine (direct call, no subprocess)."""
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
