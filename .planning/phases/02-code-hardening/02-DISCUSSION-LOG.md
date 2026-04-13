# Phase 2: Code Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 02-code-hardening
**Mode:** --auto (all decisions auto-selected)
**Areas discussed:** Packaging scope, Error handling strategy, Ruff rule set, Mypy strictness

---

## Packaging Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Metadata-only with dependencies | pyproject.toml for metadata + tool configs, install via git clone | ✓ |
| Installable package with entry points | pip install -e . with console_scripts | |
| Full uv_build package | Build backend for distribution | |

**User's choice:** [auto] Metadata-only with dependencies (recommended default)
**Notes:** Project installs via git clone per PROJECT.md constraints. No need for entry points or distribution packaging at v1.

---

## Error Handling Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| All entry-point scripts | Consistent explicit errors across save_raw_log, auto_memo, compile_logs, session_context | ✓ |
| Only save_raw_log.py | Minimum fix per CODE-03 requirement | |
| Graceful fallback with warning | Print warning but continue with default path | |

**User's choice:** [auto] All entry-point scripts (recommended default)
**Notes:** Consistent behavior is better than fixing one script. Silent failures are the anti-pattern to eliminate.

---

## Ruff Rule Set

| Option | Description | Selected |
|--------|-------------|----------|
| Standard (E, F, W, I) | Catches real bugs, enforces style, not pedantic | ✓ |
| Strict (+ UP, B, SIM, RUF) | Adds modernization and simplification rules | |
| Minimal (E, F only) | Just error detection | |

**User's choice:** [auto] Standard (E, F, W, I) (recommended default)
**Notes:** Single-maintainer project, standard rules balance quality with pragmatism. Line length 120.

---

## Mypy Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Basic on core modules | memo_engine.py + auto_memo.py, ignore-missing-imports | ✓ |
| Strict mode | Full strict checking, all modules | |
| All modules basic | Every .py file, basic mode | |

**User's choice:** [auto] Basic on core modules (recommended default)
**Notes:** Core modules are where type bugs matter most. Third-party stubs missing for sentence-transformers/mcp.

---

## Claude's Discretion

- Exact pinned versions for requirements.txt
- Ruff rule exceptions for existing code patterns
- py.typed marker file decision

## Deferred Ideas

None — discussion stayed within phase scope.
