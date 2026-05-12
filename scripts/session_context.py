#!/usr/bin/env python3
"""
session_context.py — SessionStart hook.

Detects the current project (from git or cwd), loads the project note
and last 5 relevant decisions from the vault, and injects them as
additionalContext so Claude starts the session already knowing
your past decisions.

Runs in <2s (no embedding model needed — uses SQLite only).
"""

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

# Cache git project name per cwd to keep SessionStart fast on slow
# filesystems (Dropbox CloudStorage paging git config) — N-M-5/9.
_CACHE_DIR = os.path.expanduser("~/.cache/memo")
_CACHE_PATH = os.path.join(_CACHE_DIR, "project-by-cwd.json")
_CACHE_TTL_SECONDS = 24 * 3600


def _load_cache() -> dict:
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        os.replace(tmp, _CACHE_PATH)
    except OSError:
        pass


def get_project_name(cwd: str) -> str | None:
    """Detect project name from git remote or directory name."""
    cache_key = hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:16]
    cache = _load_cache()
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and time.time() - cached.get("ts", 0) < _CACHE_TTL_SECONDS:
        name = cached.get("name")
        if isinstance(name, str) and name:
            return name

    name: str | None = None
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=3,
            cwd=cwd,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            slug = url.rstrip("/").split("/")[-1]
            slug = slug.replace(".git", "")
            if slug:
                name = slug.lower()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    if not name:
        name = os.path.basename(cwd).lower() or None

    if name:
        cache[cache_key] = {"name": name, "ts": time.time(), "cwd": cwd}
        _save_cache(cache)

    return name


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _project_aliases(project_name: str) -> set[str]:
    """Generate alias variants for fuzzy project matching.

    Covers: original, lower, hyphen→underscore, hyphen-stripped.
    Worktree forks (`claude-memo-dev`, `claude-memo.worktree`) are
    handled by the anchored prefix LIKE below, not here.
    """
    base = project_name.lower()
    return {
        base,
        base.replace("-", "_"),
        base.replace("_", "-"),
        _SLUG_RE.sub("", base),
    }


def load_project_context(vault_path: str, project_name: str) -> str | None:
    """Load project note and recent decisions from SQLite.

    Three-tier project match (N-H-J):
      1. Exact lower(project) match
      2. Match against any alias variant
      3. Anchored prefix `lower(project) LIKE base || '-%'` to catch
         worktree forks like `claude-memo-dev`. Drops the previous
         unbounded `%memo%` which collided with unrelated repos
         containing "memo" as substring.
    """
    db_path = os.path.join(vault_path, ".memo", "index.db")
    if not os.path.exists(db_path):
        return None

    aliases = _project_aliases(project_name)
    # Build a CTE-like list of acceptable project values
    placeholders = ",".join("?" for _ in aliases)
    prefix_pattern = f"{project_name.lower()}-%"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        context_parts: list[str] = []

        def fetch(query_tail: str, args: tuple, limit: int):
            sql = (
                "SELECT filepath, title, body, created FROM notes WHERE "
                + query_tail
                + f" ORDER BY created DESC LIMIT {int(limit)}"
            )
            return conn.execute(sql, args).fetchall()

        # 1. Project note (type=project)
        project_rows = fetch(
            f"type='project' AND (LOWER(project) IN ({placeholders}) OR LOWER(project) LIKE ?)",
            tuple(aliases) + (prefix_pattern,),
            1,
        )
        if project_rows:
            row = project_rows[0]
            body = row["body"]
            if len(body) > 800:
                body = body[:800] + "..."
            context_parts.append(f"## Project: {row['title']}\n{body}")

        # 2. Recent decisions
        decisions = fetch(
            f"type='decision' AND (LOWER(project) IN ({placeholders}) OR LOWER(project) LIKE ?)",
            tuple(aliases) + (prefix_pattern,),
            5,
        )
        if decisions:
            dec_lines = ["## Recent decisions:"]
            for d in decisions:
                snippet = (d["body"] or "")[:200].replace("\n", " ").strip()
                dec_lines.append(f"- **{d['title']}** ({d['created']}): {snippet}")
            context_parts.append("\n".join(dec_lines))

        # 3. Recent debug-logs
        debugs = fetch(
            f"type='debug' AND (LOWER(project) IN ({placeholders}) OR LOWER(project) LIKE ?)",
            tuple(aliases) + (prefix_pattern,),
            3,
        )
        if debugs:
            debug_lines = ["## Recent bugs solved:"]
            for d in debugs:
                debug_lines.append(f"- {d['title']} ({d['created']})")
            context_parts.append("\n".join(debug_lines))

        conn.close()

        if not context_parts:
            return None

        header = (
            f"[Engineering Brain] Context for project '{project_name}'. "
            "Use /memo find to search for details. Use /memo to save new knowledge.\n\n"
        )
        return header + "\n\n".join(context_parts)

    except sqlite3.Error:
        return None


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cwd = hook_input.get("cwd", os.getcwd())

    sys.path.insert(0, os.path.dirname(__file__))
    from memo_utils import resolve_vault_path

    try:
        vault_path = resolve_vault_path(sys.argv)
    except SystemExit:
        # Missing MEMO_VAULT_PATH should not block SessionStart silently.
        # We just skip context injection; the hook is non-essential.
        sys.exit(0)

    project_name = get_project_name(cwd)
    if not project_name:
        sys.exit(0)

    context = load_project_context(vault_path, project_name)
    if context:
        output = {"additionalContext": context}
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
