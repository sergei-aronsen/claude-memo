---
phase: "03"
fixed_at: 2026-04-13T00:00:00Z
review_path: .planning/phases/03-documentation/03-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-04-13
**Source review:** .planning/phases/03-documentation/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (1 High + 3 Medium; Low/Info excluded by fix_scope)
- Fixed: 4
- Skipped: 0

## Fixed Issues

### HR-01: Shell variable expansion silently fails in JSON hook command

**Files modified:** `examples/hooks.json`, `scripts/auto_memo_hook.sh`
**Commit:** 24dbea7
**Applied fix:** Removed `$MEMO_VAULT_PATH` argument from the SessionEnd hook command in `examples/hooks.json`. Updated `auto_memo_hook.sh` to read vault path from `${MEMO_VAULT_PATH:-$HOME/memo-vault}` environment variable instead of `$1`. Also updated the usage comment in the script to reflect the new invocation style.

### MR-01: pyproject.toml missing [build-system] table

**Files modified:** `pyproject.toml`
**Commit:** e6869b3
**Applied fix:** Added `[build-system]` table with `requires = ["uv_build>=0.11.6,<0.12"]` and `build-backend = "uv_build"` as specified in project CLAUDE.md stack decisions.

### MR-02: anthropic package missing from dependencies

**Files modified:** `pyproject.toml`
**Commit:** e6869b3
**Applied fix:** Added `auto = ["anthropic>=0.30"]` under `[project.optional-dependencies]`. The `anthropic` package is a runtime requirement for `auto_memo.py`, `session_context.py`, and `compile_logs.py` but is optional for users who only use manual `/memo` commands.

### MR-03: Dependency versions pin non-existent releases

**Files modified:** `pyproject.toml`
**Commit:** e6869b3
**Applied fix:** Replaced `sentence-transformers==5.4.0` with `sentence-transformers>=3.0,<4` and `numpy==2.4.4` with `numpy>=1.26,<3`. Also relaxed `PyYAML==6.0.3` to `PyYAML>=6.0` and `mcp[cli]==1.27.0` to `mcp[cli]>=1.0` to avoid pinning to potentially non-existent patch versions.

---

_Fixed: 2026-04-13_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
