---
phase: 02-code-hardening
plan: 03
subsystem: scripts
tags: [linting, type-checking, ruff, mypy, code-quality]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [ruff-clean, mypy-clean]
  affects: [all-scripts]
tech_stack:
  added: [ruff==0.15.10, mypy==1.15.0]
  patterns: [type-annotations, noqa-with-reason, assert-for-narrowing]
key_files:
  modified:
    - scripts/memo_engine.py
    - scripts/auto_memo.py
    - scripts/compile_logs.py
    - scripts/memo_mcp_server.py
    - scripts/memo_utils.py
    - scripts/save_raw_log.py
    - scripts/session_context.py
    - scripts/pre_compact_save.py
    - scripts/should_suggest_memo.py
decisions:
  - "Used dict[str, Any] for issues dict in lint_vault() — avoids union-attr errors while keeping code readable"
  - "Used assert for embeddings narrowing in EmbeddingsStore.add() — correct invariant, not a type: ignore"
  - "Added type: ignore[import-untyped] for yaml import — types-PyYAML is optional, not required"
  - "Moved memo_utils import to top of memo_engine.py — fixes E402 without noqa suppression"
  - "Used noqa: E402 with comment only for mcp import in memo_mcp_server.py — sys.path.insert required before it"
metrics:
  duration: 7min
  completed: "2026-04-13"
  tasks_completed: 2
  files_modified: 9
requirements_satisfied: [CODE-04, CODE-05]
---

# Phase 02 Plan 03: Ruff and Mypy — Zero-Error Code Quality Summary

**One-liner:** Ruff linting (zero errors, 9 files) and mypy type-checking (zero errors, 2 critical modules) by fixing real violations rather than suppressing them.

## What Was Built

Installed ruff==0.15.10 and mypy==1.15.0 via `uv tool install`, then fixed all lint and type violations across the codebase.

### Task 1: Ruff violations fixed (commit c585255)

Started with 25 ruff violations across 5 files. After `ruff check --fix --unsafe-fixes` auto-fixed 18, 7 remained:

| Violation | File | Fix Applied |
|-----------|------|-------------|
| E402 (memo_utils import after class defs) | memo_engine.py | Moved import to top of file |
| E402 (mcp import after sys.path.insert) | memo_mcp_server.py | Added `# noqa: E402` with reason comment |
| E501 (130 chars) prompt string | auto_memo.py | Split f-string opener onto two lines |
| E501 (122 chars) memo_log call | auto_memo.py | Extracted `saved_names` variable |
| E501 (132 chars) prompt string | compile_logs.py | Split f-string opener onto two lines |
| E501 (130 chars) list comprehension | memo_engine.py | Reformatted as multiline list comp |
| E501 (130 chars) prompt string | memo_engine.py | Split f-string opener onto two lines |

Also removed dead code: set comprehension `{r["title"] for r in rows}` whose result was never used.

`ruff format scripts/` applied consistent formatting to all 9 files.

### Task 2: Mypy errors fixed (commit 92adf73)

Started with 24 mypy errors across memo_engine.py and memo_utils.py (memo_utils is imported by both targets). After fixes: 0 errors.

**memo_utils.py fixes (8 errors → 0):**
- `call_llm(system: str = None)` → `str | None = None` (Pitfall 3 from RESEARCH.md)
- `call_haiku(system: str = None)` → `str | None = None`
- `_parse_frontmatter_basic`: annotated `meta` as `dict[str, str | list[str]]`, `current_list` as `list[str] | None`
- `import yaml` → added `# type: ignore[import-untyped]` with comment explaining types-PyYAML is optional

**memo_engine.py fixes (16 errors → 0):**
- `EmbeddingsStore.__init__`: typed `embeddings` as `np.ndarray | None`, `id_map` as `list[int]`
- `ObsidianCLI.__init__`: typed `_available` as `bool | None` (was `None`, got bool assigned)
- `EmbeddingsStore.add()`: added `assert self.embeddings is not None` before indexed assignment — correct invariant (id_map non-empty implies embeddings loaded)
- `vault_stats()`: annotated `all_links` as `set[str]`, `tag_freq` as `dict[str, int]`
- `get_vault_info()`: typed `info` as `dict[str, bool | list[str] | int | dict[str, int]]`
- `lint_vault()`: typed `issues` as `dict[str, Any]` — dict holds lists for 7 checks, then `_summary` dict; `Any` avoids spurious union-attr errors while keeping code readable
- `lint_vault()`: typed `all_link_targets` as `set[str]`, `incoming` as `dict[str, set[str]]`
- `find_duplicates()`: typed `pairs` as `list[dict[str, Any]]` — enables `.sort(key=lambda x: x["similarity"])` type inference
- Added `from typing import Any` import

## Verification Results

```
ruff check scripts/         ✓ No issues found (9 files)
ruff format --check scripts/ ✓ 9 files already formatted
mypy scripts/memo_engine.py scripts/auto_memo.py  ✓ No issues found
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed dead set comprehension in vault_stats()**
- **Found during:** Task 2 (mypy analysis)
- **Issue:** `{r["title"] for r in rows}` on line 541 — result was computed but never assigned, pure dead code. The variable `all_titles` was supposed to be here but was already removed in Task 1 (F841).
- **Fix:** Removed the orphaned set comprehension entirely
- **Files modified:** scripts/memo_engine.py
- **Commit:** 92adf73 (included in mypy fix commit)

## Known Stubs

None — all code paths produce real data, no placeholder values introduced.

## Threat Flags

None — this plan only runs linting/type-checking tools on existing code. No new trust boundaries introduced.

## Self-Check

- [x] scripts/memo_engine.py exists and is modified
- [x] scripts/auto_memo.py exists and is modified
- [x] scripts/memo_utils.py exists and is modified
- [x] Commit c585255 exists (ruff fixes)
- [x] Commit 92adf73 exists (mypy fixes)
- [x] `ruff check scripts/` exits 0
- [x] `mypy scripts/memo_engine.py scripts/auto_memo.py` exits 0

## Self-Check: PASSED
