# Phase 2: Code Hardening - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Add standard Python packaging metadata, linting/type-checking tooling, pinned dependencies, and defensive error handling to the existing codebase. No new features, no restructuring — hardening what exists.

</domain>

<decisions>
## Implementation Decisions

### Packaging Scope
- **D-01:** `pyproject.toml` is metadata-only with dependencies listed — NOT an installable package with entry points. Project installs via `git clone` + `pip install -r requirements.txt` per existing workflow. pyproject.toml provides project metadata and tool configs (ruff, mypy sections) as required by CODE-01.
- **D-02:** `requirements.txt` keeps its role as the install mechanism but versions must be pinned to specific releases (not `>=` ranges) per CODE-02.

### Error Handling Strategy
- **D-03:** All scripts that read `MEMO_VAULT_PATH` env var must fail explicitly with stderr message + non-zero exit when the var is missing AND no `--vault` arg is provided AND default `~/memo-vault` doesn't exist. Current silent fallback pattern is the bug to fix (CODE-03).
- **D-04:** `save_raw_log.py` is the priority fix (called out in requirements), but apply the same pattern to other entry-point scripts (`auto_memo.py`, `compile_logs.py`, `session_context.py`) for consistency.

### Ruff Rule Set
- **D-05:** Enable standard rule categories: E (pycodestyle errors), F (pyflakes), W (pycodestyle warnings), I (isort). This catches real bugs and enforces consistent style without being overly pedantic.
- **D-06:** Ruff config goes in `pyproject.toml` `[tool.ruff]` section. Line length 120 (matches existing code style). Target Python 3.10+.

### Mypy Strictness
- **D-07:** Basic mypy checking (not strict mode) on critical modules: `memo_engine.py` and `auto_memo.py`. These are the core logic modules where type bugs would be most impactful.
- **D-08:** Mypy config goes in `pyproject.toml` `[tool.mypy]` section. Use `--ignore-missing-imports` for third-party libs without stubs (sentence-transformers, mcp).

### Claude's Discretion
- Exact pinned versions in `requirements.txt` — Claude picks current stable versions at execution time
- Specific ruff rules to disable if any conflict with existing code patterns (pragmatic over dogmatic)
- Whether to add `py.typed` marker file (depends on whether mypy needs it for the flat layout)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in ROADMAP.md success criteria and decisions above.

### Project Constraints
- `CLAUDE.md` — Technology stack section documents recommended tooling (uv_build, ruff, mypy, pytest)
- `.planning/REQUIREMENTS.md` — CODE-01 through CODE-05 are the binding requirements
- `.planning/ROADMAP.md` — Phase 2 success criteria define what "done" means

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/memo_utils.py` — Shared utility module, likely imported by other scripts
- `scripts/memo_engine.py` — Core engine with CLI via argparse, most complex module (~40+ imports)
- `requirements.txt` — Existing dependency list (needs version pinning)

### Established Patterns
- All scripts use `#!/usr/bin/env python3` shebang
- Scripts read `MEMO_VAULT_PATH` env var with `os.environ.get()` fallback pattern
- `memo_engine.py` uses argparse for CLI
- Hook scripts (`save_raw_log.py`, `auto_memo.py`, `session_context.py`) read JSON from stdin

### Integration Points
- `pyproject.toml` is a new file — no existing packaging config to migrate from
- `requirements.txt` exists and needs version pinning (currently uses `>=` ranges)
- All 9 Python files in `scripts/` are targets for ruff linting
- `memo_engine.py` and `auto_memo.py` are mypy targets

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. CLAUDE.md technology stack section provides detailed recommendations for tooling choices (ruff >=0.9, mypy >=1.8, uv_build backend).

Note: CLAUDE.md recommends `uv_build` as build backend, but since this project is NOT an installable package (D-01), the build backend choice is less critical — pyproject.toml is primarily for metadata and tool config.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-code-hardening*
*Context gathered: 2026-04-13*
