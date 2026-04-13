---
phase: 02-code-hardening
reviewed: 2026-04-13T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - pyproject.toml
  - requirements.txt
  - scripts/auto_memo.py
  - scripts/compile_logs.py
  - scripts/memo_engine.py
  - scripts/memo_mcp_server.py
  - scripts/memo_utils.py
  - scripts/pre_compact_save.py
  - scripts/save_raw_log.py
  - scripts/session_context.py
  - scripts/should_suggest_memo.py
findings:
  critical: 2
  warning: 8
  info: 5
  total: 15
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-13
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed all 11 source files in the `scripts/` directory plus project configuration. The codebase is generally well-structured with consistent patterns. The main concerns fall into three areas:

1. **Path traversal / injection risks** — vault path and transcript path values flow from environment variables and stdin into file system operations without sanitization. An attacker controlling the hook input JSON could escape the vault boundary.
2. **Bare `except Exception` swallowing errors silently** — used extensively, which hides real failures and makes debugging impossible. Several critical code paths (API calls, file writes, subprocess invocations) silently continue on error.
3. **Hash truncation bug** — `reindex_vault` uses only the first 16 chars of a SHA-256 hash for change detection, introducing a high collision probability that will cause the incremental indexer to skip re-indexing changed files.

---

## Critical Issues

### CR-01: Path traversal via vault_path and transcript_path from untrusted input

**File:** `scripts/save_raw_log.py:89-120`, `scripts/pre_compact_save.py:29-56`, `scripts/session_context.py:120-148`, `scripts/auto_memo.py:192-208`

**Issue:** All hook scripts accept `transcript_path` from stdin JSON (controlled by the Claude Code hook system) and `vault_path` from `MEMO_VAULT_PATH` env or `--vault` CLI arg. Neither value is validated before being used in `open()`, `os.path.join()`, `os.makedirs()`, and `subprocess.run()`. A malicious or buggy hook input such as `{"transcript_path": "../../etc/passwd"}` would be opened directly. While the threat model here is local (own machine) and the hook system is trusted, injecting a `transcript_path` value via a compromised Claude session is a realistic scenario given the project's purpose of processing session transcripts.

**Fix:** Canonicalize and validate both paths before use:
```python
import pathlib

def safe_path(base: str, candidate: str) -> str | None:
    """Return resolved path only if it stays within base, else None."""
    try:
        resolved = pathlib.Path(candidate).resolve()
        base_resolved = pathlib.Path(base).resolve()
        resolved.relative_to(base_resolved)  # raises ValueError if outside
        return str(resolved)
    except (ValueError, OSError):
        return None

# For transcript_path (does not need to be inside vault):
transcript_path = pathlib.Path(transcript_path).resolve()
# At minimum, reject paths with null bytes and ensure existence check is done
# before opening, as already done in auto_memo.py line 204.
```

For `transcript_path`, which legitimately lives outside the vault (it's a Claude Code internal file), the minimum hardening is: reject if it contains `..` components or null bytes, and verify `os.path.isabs(transcript_path)`.

---

### CR-02: SHA-256 hash truncated to 16 hex chars — high collision rate in incremental reindex

**File:** `scripts/memo_engine.py:616`

**Issue:** `reindex_vault` computes `hashlib.sha256(open(abs_path, "rb").read()).hexdigest()[:16]` (only 16 hex chars = 64 bits of hash). The `index_file` function called for new files stores the full 256-bit hash via `compute_file_hash()`. This means the stored hash and the comparison hash use different lengths. The `existing[rel_path][0] == file_hash` comparison at line 617 will never match because the stored hash is 64 chars and the computed comparison hash is 16 chars. As a result, incremental reindex will always treat every file as changed and re-index it — defeating the optimization entirely. This is a silent correctness bug, not a crash.

**Fix:**
```python
# Line 616 — remove the [:16] slice, use the full hash
file_hash = hashlib.sha256(open(abs_path, "rb").read()).hexdigest()
# Consistent with compute_file_hash() which returns the full hexdigest
```

---

## Warnings

### WR-01: Bare `except Exception: pass` swallows all errors in critical paths

**File:** `scripts/memo_utils.py:407-408`, `scripts/memo_utils.py:435-436`, `scripts/memo_utils.py:465-467`, `scripts/auto_memo.py:98-101`, `scripts/compile_logs.py:60-62`

**Issue:** Failures in `save_memo()` (file write), `append_to_index()` (index update), and `index_memo_file()` (search index) are silently discarded. If the vault directory becomes unwritable or the subprocess crashes, the caller sees `None` returned but no log entry, no error message, and no indication of why. This makes production debugging extremely difficult. The pattern appears 10+ times across the codebase.

**Fix:** At minimum, log the exception before swallowing it:
```python
except Exception as e:
    memo_log(vault_path, f"Failed to write memo: {e}", "save_memo")
    return None
```
For `index_memo_file` in `memo_utils.py`, the subprocess call at line 461 uses `capture_output=True` which suppresses stderr. If the subprocess fails, the exception is swallowed at line 465. Add:
```python
except Exception as e:
    # Log but don't crash — indexing failure is non-fatal
    import sys
    print(f"[memo] index warning: {e}", file=sys.stderr)
```

---

### WR-02: `find_duplicates` returns dict format but `memo_mcp_server.py` reads `title_a`/`title_b` keys that don't exist

**File:** `scripts/memo_mcp_server.py:310`, `scripts/memo_engine.py:493-497`

**Issue:** `find_duplicates()` returns pairs with keys `note_a` (dict with `title`, `id`, `path`) and `note_b`. But `memo_mcp_server.py` line 310 reads `p['title_a']` and `p['title_b']` which are not in the returned dicts. This will raise a `KeyError` at runtime whenever duplicates are found.

**Fix:** Either change `memo_engine.py:find_duplicates` to flatten the keys:
```python
pairs.append({
    "title_a": row_a["title"],
    "title_b": row_b["title"],
    "path_a": row_a["filepath"],
    "path_b": row_b["filepath"],
    "similarity": round(float(sim_matrix[i, j]), 3),
})
```
Or fix the consumer in `memo_mcp_server.py:310`:
```python
lines.append(f"- {p['note_a']['title']} ↔ {p['note_b']['title']} (similarity: {p['similarity']:.2f})")
```

---

### WR-03: `lint_vault` builds a dict literal and immediately discards it (dead code / logic error)

**File:** `scripts/memo_engine.py:796`

**Issue:** Line 796 is `{row["filepath"]: row["title"] for row in all_notes}` — a dict comprehension whose result is never assigned to a variable. This was likely meant to be `filepath_to_title = {row["filepath"]: row["title"] for row in all_notes}` but the assignment was omitted. The variable is never used below, but its omission is a logic error indicating that subsequent code that might have needed this lookup is broken or missing.

**Fix:**
```python
# Either assign it for future use:
filepath_to_title = {row["filepath"]: row["title"] for row in all_notes}
# Or delete the line entirely if it's genuinely unused.
```

---

### WR-04: `VaultLock` does not close the lock file on exception during `__exit__`

**File:** `scripts/memo_engine.py:113-116`

**Issue:** In `VaultLock.__exit__`, if `fcntl.flock(self.lock_file, fcntl.LOCK_UN)` raises (which is rare but possible on NFS), `self.lock_file.close()` is never called, leaking the file descriptor. Additionally, if `open(self.lock_path, "w")` in `__enter__` succeeds but the second `flock` call (blocking wait) is interrupted by a signal, `__exit__` will still be called, but `self.lock_file` is open and not yet locked — the unlock in `__exit__` will operate on an unlocked file, which is harmless but misleading.

**Fix:**
```python
def __exit__(self, *args):
    if self.lock_file:
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
        finally:
            self.lock_file.close()
            self.lock_file = None
```

---

### WR-05: `session_context.py` injects project name directly into SQLite LIKE pattern without escaping

**File:** `scripts/session_context.py:55-70`

**Issue:** `project_name` is derived from the git remote URL or directory name and inserted directly into a SQLite `LIKE` pattern: `f"%{project_name}%"`. SQLite `LIKE` treats `%` and `_` as wildcards. If a project name contains these characters (e.g., a directory named `100%_done`), the query would match unintended rows. While not a SQL injection risk (parameterized query is used), it is a correctness bug.

**Fix:**
```python
# Escape LIKE special characters in project_name
safe_name = project_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
conn.execute(
    "... LIKE ? ESCAPE '\\'",
    (project_name, f"%{safe_name}%"),
)
```

---

### WR-06: `save_raw_log.py` opens log file without encoding specified

**File:** `scripts/save_raw_log.py:133`

**Issue:** `open(memo_log, "a")` at line 133 does not specify `encoding="utf-8"`. On Windows or systems with non-UTF-8 locale, this will use the platform default encoding and may fail or corrupt log entries containing non-ASCII characters (e.g., Russian text in session IDs or file names).

**Fix:**
```python
with open(memo_log, "a", encoding="utf-8") as f:
    f.write(...)
```

---

### WR-07: `memo_mcp_server.py` `memo_save` uses mutable default argument `tags: list[str] = None`

**File:** `scripts/memo_mcp_server.py:132-133`

**Issue:** The function signature `def memo_save(..., tags: list[str] = None, aliases: list[str] = None, ...)` uses `None` as default which is fine, but the type annotation says `list[str]` rather than `list[str] | None`. This is a type annotation error that will cause mypy or strict type checkers to flag incorrect usage. Additionally, the body correctly handles `tags or []`, so runtime behavior is correct — but the signature is misleading.

**Fix:**
```python
def memo_save(
    ...
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
    ...
) -> str:
```

---

### WR-08: `compile_logs.py` `find_uncompiled_logs` skips ALL auto-processed logs, including partial ones

**File:** `scripts/compile_logs.py:55-57`

**Issue:** Any log file containing the string `<!-- auto-processed` anywhere is skipped entirely (line 56). The `AUTO_PROCESSED_MARKER` check is correct in intent, but `auto_memo.py` appends `<!-- auto-processed session=XXXX -->` only once per session, while a daily log file can accumulate entries from multiple sessions (some auto-processed, some not). A log with mixed sessions — one auto-processed, others not — will be silently skipped, meaning the non-auto-processed sessions are never compiled.

**Fix:** Either track processed session IDs more granularly, or change the behavior so `compile_logs` processes the log if ANY session in it was not auto-processed. At minimum, document this known limitation:
```python
# Current behavior: if any session in this log was auto-processed,
# the entire log is skipped. This means mixed-session logs (some auto-
# processed, some not) are never compiled for the non-processed sessions.
if AUTO_PROCESSED_MARKER in content:
    continue
```

---

## Info

### IN-01: `memo_engine.py` `reindex_vault` opens file without context manager in incremental path

**File:** `scripts/memo_engine.py:616`

**Issue:** `hashlib.sha256(open(abs_path, "rb").read()).hexdigest()` opens the file without a `with` block. If `sha256()` call raises (impossible here, but pattern is fragile), the file handle leaks.

**Fix:**
```python
with open(abs_path, "rb") as fh:
    file_hash = hashlib.sha256(fh.read()).hexdigest()
```

---

### IN-02: `auto_memo.py` deferred import pattern is inconsistent

**File:** `scripts/auto_memo.py:166-167`, `scripts/auto_memo.py:181-182`, `scripts/auto_memo.py:187-188`

**Issue:** `memo_utils` functions are imported inside function bodies rather than at module top level. This is inconsistent with `compile_logs.py` which imports at the top. Deferred imports hide import errors until the function is called, making it harder to detect installation issues at startup.

**Fix:** Move all `from memo_utils import ...` to the top of the file, after `sys.path` manipulation if needed.

---

### IN-03: Magic number `4` used as minimum message threshold in multiple files

**File:** `scripts/auto_memo.py:212`, `scripts/save_raw_log.py:123`, `scripts/pre_compact_save.py:84`

**Issue:** The minimum message count check (`if len(messages) < 4`) appears in three files with the same value but no named constant. `pre_compact_save.py` uses `3` instead of `4`, which is inconsistent.

**Fix:** Define a shared constant in `memo_utils.py`:
```python
MIN_SESSION_MESSAGES = 4  # Skip sessions shorter than this
```
And import it in each script.

---

### IN-04: `build_frontmatter` in `memo_utils.py` does not quote `None` values

**File:** `scripts/memo_utils.py:114`

**Issue:** `lines.append(f"{key}: {value}")` — if `value` is Python `None`, this writes `key: None` to YAML, which YAML parsers will correctly read back as `null`. However, `False`, `0`, and empty strings would also be written as bare values. This works with PyYAML's `safe_load`, but the basic fallback parser `_parse_frontmatter_basic` would parse `None` as the string `"None"` (line 89: `value = stripped[idx + 1:].strip().strip("'\"")`).

**Fix:** In `build_frontmatter`, explicitly convert None:
```python
if value is None:
    lines.append(f"{key}: null")
else:
    # existing logic
```

---

### IN-05: `memo_mcp_server.py` `memo_find_duplicates` return value inconsistency

**File:** `scripts/memo_mcp_server.py:308-311`

**Issue:** The `memo_find_duplicates` tool calls `find_duplicates` which returns a list of dicts with `note_a`/`note_b` nested dicts. However the tool's display code at line 310 accesses `p['title_a']` (documented in WR-02 above as a KeyError). Beyond the crash risk, the `pairs[:10]` slice silently drops pairs beyond 10 with no user notification.

**Fix:** Surface the total count:
```python
lines.append(f"Found {len(pairs)} potential duplicate pair(s) (showing first {min(10, len(pairs))}):\n")
```

---

_Reviewed: 2026-04-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
