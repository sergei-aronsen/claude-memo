# Phase 02: Code Hardening - Research

**Researched:** 2026-04-13
**Domain:** Python packaging, linting (ruff), type checking (mypy), defensive error handling
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `pyproject.toml` is metadata-only with dependencies listed — NOT an installable package with entry points. Project installs via `git clone` + `pip install -r requirements.txt`. pyproject.toml provides project metadata and tool configs (ruff, mypy sections).
- **D-02:** `requirements.txt` keeps its role as the install mechanism but versions must be pinned to specific releases (not `>=` ranges).
- **D-03:** All scripts that read `MEMO_VAULT_PATH` env var must fail explicitly with stderr message + non-zero exit when the var is missing AND no `--vault` arg is provided AND default `~/memo-vault` doesn't exist. Current silent fallback pattern is the bug to fix.
- **D-04:** `save_raw_log.py` is the priority fix, but apply the same pattern to `auto_memo.py`, `compile_logs.py`, `session_context.py` for consistency.
- **D-05:** Enable ruff rule categories: E (pycodestyle errors), F (pyflakes), W (pycodestyle warnings), I (isort).
- **D-06:** Ruff config in `[tool.ruff]` section, line length 120, target Python 3.10+.
- **D-07:** Basic mypy checking (not strict mode) on `memo_engine.py` and `auto_memo.py`.
- **D-08:** Mypy config in `[tool.mypy]` section. Use `--ignore-missing-imports` for third-party libs without stubs.

### Claude's Discretion
- Exact pinned versions in `requirements.txt` — Claude picks current stable versions at execution time
- Specific ruff rules to disable if any conflict with existing code patterns (pragmatic over dogmatic)
- Whether to add `py.typed` marker file (depends on whether mypy needs it for the flat layout)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CODE-01 | `pyproject.toml` created with project metadata, dependencies, and tool configs (ruff, mypy) | PEP 621 `[project]` table + `[tool.ruff]` + `[tool.mypy]` sections |
| CODE-02 | Dependency versions pinned in requirements.txt (sentence-transformers, etc.) | Verified current stable versions via pip registry |
| CODE-03 | `save_raw_log.py` fails with explicit stderr message when `MEMO_VAULT_PATH` not set | Error handling pattern documented in Architecture Patterns section |
| CODE-04 | ruff configuration added — lint + format rules for consistent code style | Ruff 0.15.10 config documented with known rule conflicts |
| CODE-05 | mypy configuration added — type checking for critical modules | Mypy 1.20.1 config documented with --ignore-missing-imports strategy |
</phase_requirements>

## Summary

Phase 2 adds Python packaging infrastructure and code quality tooling to an existing flat-layout codebase (`scripts/` directory, 9 Python files). The project is NOT a distributable package — it installs via git clone. This means `pyproject.toml` serves purely as a metadata + tool-config file, not a build specification. No entry points, no src/ layout restructure needed.

The critical hardening task (CODE-03) fixes a silent failure mode in `save_raw_log.py`: when `MEMO_VAULT_PATH` is unset and `--vault` is not provided, the script currently falls back silently to `~/memo-vault` even if that directory doesn't exist. The fix must print to stderr and exit non-zero when all three conditions fail (no env var, no `--vault` arg, and default `~/memo-vault` doesn't exist). The same three-step check pattern must be applied to `session_context.py` and `pre_compact_save.py` (which use `os.environ.get("MEMO_VAULT_PATH", os.path.expanduser("~/memo-vault"))` without existence check).

Ruff 0.15.10 and mypy 1.20.1 are the current stable versions as of April 2026. The codebase uses Python 3.10+ syntax (`str | None` union syntax, `list[dict]` generics) — targeting `py310` in both ruff and mypy is correct. Known potential ruff violations in the existing code include bare `except Exception:` clauses (E722), unused imports, and long lines in `memo_engine.py`. These will need targeted `# noqa` suppressions or code fixes, not wholesale rule disabling.

**Primary recommendation:** Write `pyproject.toml` first (CODE-01), pin requirements.txt second (CODE-02), then fix error handling (CODE-03), then run ruff to surface violations and fix/suppress them (CODE-04), then run mypy on critical modules (CODE-05). Each step verifiable independently.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | 0.15.10 | Linting + formatting (replaces flake8 + black + isort) | Current latest [VERIFIED: pip registry]; CLAUDE.md mandates `>=0.9` |
| mypy | 1.20.1 | Static type checking | Current latest [VERIFIED: pip registry]; CLAUDE.md mandates `>=1.8` |

### Project Dependencies (for requirements.txt pinning)
| Library | Pinned Version | Current Latest | Notes |
|---------|---------------|----------------|-------|
| sentence-transformers | 5.4.0 | 5.4.0 | [VERIFIED: pip registry + pip3 show] |
| numpy | 2.4.4 | 2.4.4 | [VERIFIED: pip registry + pip3 show] |
| PyYAML | 6.0.3 | 6.0.3 | [VERIFIED: pip registry + pip3 show] |
| mcp[cli] | 1.27.0 | 1.27.0 | [VERIFIED: pip registry + pip3 show] — optional per existing requirements.txt comment |

**Note on anthropic:** The current `requirements.txt` does NOT list `anthropic` as a dependency. Code inspection confirms no `import anthropic` in any script — `memo_utils.py` uses `urllib.request` directly for API calls. The requirements.txt comment says "optional — only needed if using memo_mcp_server.py" for mcp, and the memo_utils.py uses raw urllib. Do not add `anthropic` to requirements.txt unless the code actually imports it. [VERIFIED: grep on scripts/]

**Installation:**
```bash
pip install -r requirements.txt
# or with uv (faster):
uv pip install -r requirements.txt
```

**Version verification:** All package versions verified against live pip registry on 2026-04-13. [VERIFIED: pip3 index versions]

## Architecture Patterns

### Recommended pyproject.toml Structure
```toml
[project]
name = "claude-memo"
version = "0.1.0"
description = "Persistent engineering memory for Claude Code"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "sentence-transformers==5.4.0",
    "numpy==2.4.4",
    "PyYAML==6.0.3",
]

[project.optional-dependencies]
mcp = ["mcp[cli]==1.27.0"]

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = []  # Populated after first ruff run

[tool.ruff.lint.per-file-ignores]
# Hook scripts use bare except for resilience — acceptable
"scripts/save_raw_log.py" = ["E722"]
"scripts/pre_compact_save.py" = ["E722"]

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
warn_return_any = false
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = ["sentence_transformers.*", "mcp.*", "numpy.*"]
ignore_missing_imports = true
```

### Pattern 1: Explicit Vault Path Validation (CODE-03 Fix)
**What:** Three-condition check — env var missing AND no --vault arg AND default path doesn't exist → fail loudly.
**When to use:** Any entry-point script that reads MEMO_VAULT_PATH.
**How D-03 translates to code:**

```python
# Source: CONTEXT.md D-03 decision + inspection of save_raw_log.py lines 90-99

def main():
    vault_path = os.environ.get("MEMO_VAULT_PATH", "")

    # Also accept --vault argument
    if not vault_path:
        for i, arg in enumerate(sys.argv):
            if arg == "--vault" and i + 1 < len(sys.argv):
                vault_path = os.path.expanduser(sys.argv[i + 1])

    if not vault_path:
        default = os.path.expanduser("~/memo-vault")
        if os.path.exists(default):
            vault_path = default
        else:
            print(
                "Error: MEMO_VAULT_PATH is not set and ~/memo-vault does not exist.\n"
                "Set the environment variable: export MEMO_VAULT_PATH=/path/to/your/vault\n"
                "Or pass --vault /path/to/your/vault",
                file=sys.stderr,
            )
            sys.exit(1)
```

**Applies to:** `save_raw_log.py` (priority), `session_context.py`, `pre_compact_save.py`

**Note on auto_memo.py and compile_logs.py:** These scripts use `--vault` as a required argparse argument (`required=True`), so argparse already fails loudly if `--vault` is missing. No change needed. [VERIFIED: code inspection of auto_memo.py line 193, compile_logs.py line 135]

### Pattern 2: Requirements.txt with Pinned Versions
**What:** Exact version pins (`==`) instead of ranges (`>=`) for reproducible installs.
**Before:**
```
sentence-transformers>=2.2.0
numpy>=1.24.0
PyYAML>=6.0
mcp[cli]>=1.2.0
```
**After:**
```
# Core dependencies
sentence-transformers==5.4.0
numpy==2.4.4
PyYAML==6.0.3

# MCP Server (optional — only needed if using memo_mcp_server.py)
mcp[cli]==1.27.0
```

### Anti-Patterns to Avoid
- **Build backend in pyproject.toml when not packaging:** Since D-01 says this is NOT an installable package, do not add `[build-system]` table. A pyproject.toml without `[build-system]` is valid PEP 621 — it works for metadata and tool config. Adding `uv_build` as build backend would mislead contributors. [ASSUMED — PEP 621 allows omitting build-system for metadata-only files]
- **Strict mypy on the whole codebase:** The scripts have `Optional` types declared inconsistently and use `system: str = None` patterns that mypy strict mode rejects. Basic checking on the two critical modules is the right call (D-07).
- **Wholesale rule disabling:** Disabling E722 globally hides real bugs. Use per-file-ignores for specific scripts that intentionally use bare except for hook resilience.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Import sorting | Custom sort script | `ruff --select I` (isort rules) | Handles all edge cases: stdlib vs third-party vs local, relative imports |
| Code formatting | Manual line-length enforcement | `ruff format` | Consistent, reproducible, zero config needed beyond line-length |
| Type stub discovery | Manual stub paths | `mypy --ignore-missing-imports` | sentence-transformers, mcp, fcntl don't ship stubs — ignore-missing-imports is the standard solution |

**Key insight:** ruff replaces flake8 + isort + pycodestyle in a single tool. Running `ruff check .` covers all E/F/W/I rules simultaneously.

## Common Pitfalls

### Pitfall 1: `fcntl` Module on Windows
**What goes wrong:** mypy on Windows (or CI running Windows) will fail on `memo_engine.py` because `fcntl` is Unix-only and has no type stubs on Windows.
**Why it happens:** `fcntl` is not available on Windows — mypy correctly errors on unknown module.
**How to avoid:** Add `[[tool.mypy.overrides]]` with `ignore_missing_imports = true` for `fcntl`, OR add `# type: ignore[import]` at the import site in `memo_engine.py`. Since CI runs Linux (GitHub Actions ubuntu), this may not be a live issue — flag it as a known platform constraint.
**Warning signs:** `mypy: Cannot find implementation or library stub for module named "fcntl"`

### Pitfall 2: Ruff E501 vs Line Length 120
**What goes wrong:** `memo_engine.py` has lines longer than 88 (the ruff default) but under 120. Without explicitly setting `line-length = 120`, ruff will flag hundreds of lines.
**Why it happens:** Ruff defaults to 88 (black compatibility). The existing code was written with 120 in mind.
**How to avoid:** Set `line-length = 120` in `[tool.ruff]` as D-06 specifies. [VERIFIED: code inspection shows lines up to ~115 chars]

### Pitfall 3: `system: str = None` Default Argument Pattern
**What goes wrong:** mypy will flag `def call_haiku(prompt: str, ..., system: str = None)` — the default `None` is not compatible with type `str`.
**Why it happens:** This is a common Python pattern but is technically incorrect typing. The proper annotation is `system: str | None = None` or `Optional[str] = None`.
**How to avoid:** Since only `memo_engine.py` and `auto_memo.py` are mypy targets (D-07), and `call_haiku` is in `memo_utils.py` (not a mypy target), this won't surface in the initial run. If mypy is extended to `memo_utils.py` later, fix the signatures.

### Pitfall 4: Inline Imports Inside Functions
**What goes wrong:** `auto_memo.py` uses `from memo_utils import ...` inside function bodies (lines 169, 185, 189). Ruff does NOT flag this by default, but mypy may have issues tracing types through runtime imports.
**Why it happens:** The scripts directory is on `sys.path` only at runtime, so top-level imports were avoided.
**How to avoid:** Add `scripts/` to mypy's `mypy_path` in `[tool.mypy]` so it can resolve `memo_utils`:
```toml
[tool.mypy]
mypy_path = "scripts"
```

### Pitfall 5: `bare except` in Hook Scripts
**What goes wrong:** Hook scripts (`save_raw_log.py`, `pre_compact_save.py`) use `except Exception:` and `except:` for resilience — they must never crash the hook. Ruff E722 flags bare `except:` (without Exception type).
**Why it happens:** Intentional design for hook scripts. Ruff is correct to flag bare `except:` without `Exception` — it catches `KeyboardInterrupt` and `SystemExit` which is usually unintended.
**How to avoid:** Use `except Exception:` (not bare `except:`) everywhere. Ruff's E722 only flags the bare form. Already compliant in most places — verify with `ruff check --select E722 scripts/`.

## Code Examples

### pyproject.toml (minimal, metadata + tool config, no build-system)
```toml
# Source: PEP 621 spec, CONTEXT.md D-01 decision

[project]
name = "claude-memo"
version = "0.1.0"
description = "Persistent engineering memory for Claude Code — automatic capture and semantic search"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
keywords = ["claude", "ai", "memory", "obsidian", "knowledge-management"]
dependencies = [
    "sentence-transformers==5.4.0",
    "numpy==2.4.4",
    "PyYAML==6.0.3",
]

[project.optional-dependencies]
mcp = ["mcp[cli]==1.27.0"]

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]

[tool.ruff.lint.per-file-ignores]
# Hook scripts catch all exceptions intentionally for resilience
"scripts/save_raw_log.py" = ["E722"]
"scripts/pre_compact_save.py" = ["E722"]

[tool.mypy]
python_version = "3.10"
mypy_path = "scripts"
ignore_missing_imports = true
warn_return_any = false
warn_unused_ignores = true
```

### Running ruff and mypy
```bash
# Lint check (zero errors target)
ruff check scripts/

# Format check (don't auto-fix in CI)
ruff format --check scripts/

# Apply fixes (local development)
ruff check --fix scripts/
ruff format scripts/

# Mypy on critical modules only (D-07)
mypy scripts/memo_engine.py scripts/auto_memo.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `flake8 + black + isort` separately | `ruff` (unified) | 2022-2024 | Single tool, 100x faster, same rules |
| `setup.py` / `setup.cfg` | `pyproject.toml` (PEP 621) | Python 3.11+ standard | All modern tools read pyproject.toml |
| `>=` version ranges in requirements | `==` pinned versions | Best practice for apps (not libraries) | Reproducible installs across machines |
| `Optional[str]` from typing module | `str \| None` syntax | Python 3.10+ | Both still valid; existing code uses both |

**Deprecated/outdated:**
- `requirements.txt` with `>=` ranges: Fine for libraries, wrong for applications/tools — use `==` pins

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pyproject.toml without `[build-system]` is valid and tools won't complain | Architecture Patterns | Low — ruff and mypy read pyproject.toml regardless of build-system presence |
| A2 | `fcntl` issue with mypy only appears on non-Linux platforms (CI uses Linux) | Common Pitfalls | Low — GitHub Actions ubuntu runners have fcntl; only risk is local Windows dev |
| A3 | Inline imports in `auto_memo.py` won't cause mypy errors if `mypy_path = "scripts"` is set | Common Pitfalls | Medium — if mypy still can't resolve memo_utils, may need explicit `# type: ignore` |

**If this table is empty:** All other claims were verified or cited via tool calls.

## Open Questions (RESOLVED)

1. **Whether `py.typed` marker is needed**
   - What we know: `py.typed` signals to mypy that a package ships inline types (PEP 561). It's relevant for installable packages consumed by other code.
   - What's unclear: Since this is a flat-layout script collection (not an installable package per D-01), `py.typed` is irrelevant — mypy reads sources directly from `mypy_path = "scripts"`.
   - Recommendation: Do NOT add `py.typed`. Not applicable for non-package projects.

2. **Exact ruff ignores needed after first run**
   - What we know: E/F/W/I rules will surface some violations in the existing code (bare excepts, possibly unused imports, long lines in string literals).
   - What's unclear: Exact count and nature until `ruff check scripts/` runs for the first time.
   - Recommendation: Plan task should include a "run ruff, categorize violations, fix or suppress" step. Pre-approved suppressions: E722 per-file for hook scripts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All scripts (union type syntax) | ✓ | 3.12.13 (also 3.14.3) | — |
| pip3 | requirements.txt install | ✓ | 26.0 | uv pip |
| uv | Faster installs | ✓ | 0.9.26 | pip3 |
| ruff | CODE-04 | ✗ (not installed) | — | `pip3 install ruff==0.15.10` |
| mypy | CODE-05 | ✗ (not installed) | — | `pip3 install mypy==1.20.1` |

**Missing dependencies with no fallback:**
- `ruff` — must be installed before CODE-04 tasks can execute
- `mypy` — must be installed before CODE-05 tasks can execute

**Missing dependencies with fallback:**
- None

**Install commands for plan Wave 0:**
```bash
pip3 install ruff==0.15.10 mypy==1.20.1
# or
uv tool install ruff
uv pip install mypy==1.20.1
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None installed (pytest not yet present — deferred to v2 per REQUIREMENTS.md TEST-01) |
| Config file | None — Wave 0 gap |
| Quick run command | N/A for this phase |
| Full suite command | `ruff check scripts/ && mypy scripts/memo_engine.py scripts/auto_memo.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CODE-01 | pyproject.toml has valid PEP 621 `[project]` + tool sections | manual inspection | `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"` (Python 3.11+) | ❌ Wave 0 |
| CODE-02 | All deps pinned with `==` in requirements.txt | manual grep | `grep -E ">=" requirements.txt` should return nothing | ✓ (file exists, check is simple) |
| CODE-03 | `save_raw_log.py` exits non-zero + stderr when vault missing | smoke test | `echo '{"transcript_path":"","session_id":"x"}' \| python3 scripts/save_raw_log.py; echo $?` | ❌ test not written |
| CODE-04 | ruff passes with zero errors | automated | `ruff check scripts/` | ❌ Wave 0 (ruff not installed) |
| CODE-05 | mypy passes on critical modules | automated | `mypy scripts/memo_engine.py scripts/auto_memo.py` | ❌ Wave 0 (mypy not installed) |

### Sampling Rate
- **Per task commit:** `ruff check scripts/` (after ruff is installed)
- **Per wave merge:** `ruff check scripts/ && mypy scripts/memo_engine.py scripts/auto_memo.py`
- **Phase gate:** All commands above pass before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Install ruff and mypy: `pip3 install ruff==0.15.10 mypy==1.20.1`
- [ ] pyproject.toml does not exist yet — create it as the first task

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (partial) | `sys.argv` and env var handling — validate vault path exists before use |
| V6 Cryptography | no | — |

### Known Threat Patterns for this phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via vault_path from env var | Tampering | `os.path.exists()` check + explicit error prevents acting on attacker-controlled paths |
| Silent failure masking errors | Denial of Service | explicit stderr + sys.exit(1) on bad config (CODE-03 fix) |

## Sources

### Primary (HIGH confidence)
- `pip3 index versions` — verified all package versions against live registry on 2026-04-13
- `pip3 show` — verified installed versions of sentence-transformers (5.4.0), numpy (2.4.4), PyYAML (6.0.3), mcp (1.27.0)
- Direct codebase inspection — verified MEMO_VAULT_PATH usage patterns, import patterns, type annotations in all 9 Python scripts

### Secondary (MEDIUM confidence)
- CLAUDE.md project documentation — technology stack recommendations (ruff >=0.9, mypy >=1.8, uv_build, pytest)
- CONTEXT.md D-01 through D-08 — user-locked implementation decisions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via live pip registry
- Architecture (pyproject.toml structure): HIGH — based on PEP 621 and direct codebase audit
- Error handling pattern: HIGH — based on actual source code inspection of save_raw_log.py
- Pitfalls: HIGH for ruff/mypy issues (code-inspected), MEDIUM for fcntl/Windows (assumed Linux CI)

**Research date:** 2026-04-13
**Valid until:** 2026-07-13 (stable tools — ruff and mypy release often but not breaking)
