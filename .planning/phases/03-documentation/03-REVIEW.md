---
phase: "03"
status: findings
severity_summary:
  critical: 0
  high: 1
  medium: 3
  low: 2
  info: 3
files_reviewed: 5
files_reviewed_list:
  - README.md
  - CONTRIBUTING.md
  - CHANGELOG.md
  - examples/hooks.json
  - pyproject.toml
depth: standard
reviewed: 2026-04-13T00:00:00Z
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-13
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Five documentation and config files reviewed. No secrets or personal data exposed. The main functional bug is in `examples/hooks.json` — a shell variable `$MEMO_VAULT_PATH` embedded in a JSON string that will not be expanded at runtime, causing the SessionEnd hook to silently break. Three `USERNAME` placeholders were left unreplaced across README, CONTRIBUTING, and CHANGELOG. The `pyproject.toml` is missing a `[build-system]` table (required for `pip install .` to work) and omits the `anthropic` package from dependencies despite it being a runtime requirement for auto-memo. Two dependency version pins reference versions that likely do not exist yet.

---

## High

### HR-01: Shell variable expansion silently fails in JSON hook command

**File:** `examples/hooks.json:20`
**Issue:** The SessionEnd hook command is `"bash ~/.claude/skills/memo-skill/scripts/auto_memo_hook.sh $MEMO_VAULT_PATH"`. JSON does not perform shell variable expansion. When Claude Code reads this JSON and spawns the command, `$MEMO_VAULT_PATH` is passed as the literal four-word string — not the user's vault path. The script receives a wrong path and either crashes or silently writes to a wrong location. All other hook commands in this file correctly avoid dynamic arguments, making this inconsistency stand out further.

**Fix:** Remove the runtime-variable argument from the JSON and have the script read `MEMO_VAULT_PATH` from the environment internally (which `auto_memo_hook.sh` should already have access to via the inherited environment):
```json
"command": "bash ~/.claude/skills/memo-skill/scripts/auto_memo_hook.sh"
```
Inside `auto_memo_hook.sh`, replace the positional `$1` argument with `${MEMO_VAULT_PATH:-~/memo-vault}`. This matches how the other three hook scripts already work.

---

## Medium

### MR-01: pyproject.toml missing [build-system] table

**File:** `pyproject.toml` (entire file)
**Issue:** The file has `[project]` metadata but no `[build-system]` table. Without it, `pip install .`, `uv build`, and `uv pip install -e .` all fail or fall back to legacy behavior. The project CLAUDE.md explicitly recommends `uv_build>=0.11.6,<0.12` as the build backend. This must be present for anyone following CONTRIBUTING.md's setup instructions.

**Fix:** Add the build-system table after the `[project]` block:
```toml
[build-system]
requires = ["uv_build>=0.11.6,<0.12"]
build-backend = "uv_build"
```

### MR-02: anthropic package missing from dependencies

**File:** `pyproject.toml:9-13`
**Issue:** The `anthropic` Python package is a runtime dependency — `auto_memo.py`, `session_context.py`, and `compile_logs.py` all call the Anthropic API (Claude Haiku). It is not listed in `[project].dependencies` or any optional group. A fresh `pip install claude-memo` will install a broken package. Adding it to `[project.optional-dependencies]` under an `ai` or `auto` key would be correct (since the tool works without it for manual `/memo` use), but it must appear somewhere in the package metadata.

**Fix:**
```toml
[project.optional-dependencies]
mcp = ["mcp[cli]==1.27.0"]
auto = ["anthropic>=0.30"]
```
Update CONTRIBUTING.md and README install steps to note `pip install -r requirements.txt` should cover this, or ensure `requirements.txt` lists `anthropic`.

### MR-03: Dependency versions pin non-existent releases

**File:** `pyproject.toml:10-11`
**Issue:** `sentence-transformers==5.4.0` and `numpy==2.4.4` pin specific patch versions that do not exist as of the knowledge cutoff (April 2026). `sentence-transformers` stable was in the 3.x range; `numpy` 2.x series topped at 2.2.x. Installing this `pyproject.toml` as-is will fail with `ERROR: No matching distribution found`. If these are aspirational/future pins, they are not valid for a shipping 1.0.0.

**Fix:** Either pin to the latest known-good versions:
```toml
dependencies = [
    "sentence-transformers>=3.0,<4",
    "numpy>=1.26,<3",
    "PyYAML>=6.0",
]
```
Or, if exact pins are required for reproducibility, verify the versions exist on PyPI before publishing and cross-check with `requirements.txt`.

---

## Low

### LR-01: USERNAME placeholder left in three files

**File:** `README.md:5`, `README.md:67`, `CONTRIBUTING.md:6`, `CHANGELOG.md:38`
**Issue:** Four occurrences of the literal string `USERNAME` appear in GitHub URLs. These produce broken badge images (README line 5), a non-functional clone command (README line 67, CONTRIBUTING line 6), and a dead release link (CHANGELOG line 38). Not a security issue, but the install instructions will silently fail for any user who copy-pastes them.

**Fix:** Replace `USERNAME` with the actual GitHub username/org before publishing. All four locations:
- `README.md:5` — badge URL
- `README.md:67` — clone URL in installation step 1
- `CONTRIBUTING.md:6` — clone URL in dev setup
- `CHANGELOG.md:38` — release tag URL

### LR-02: CONTRIBUTING.md references missing dev-dependencies

**File:** `CONTRIBUTING.md:17-23`
**Issue:** The contributing guide instructs contributors to run `ruff check scripts/` and `mypy scripts/memo_engine.py`, but neither `ruff` nor `mypy` is listed as a dependency in `pyproject.toml` (no `[project.optional-dependencies.dev]` group exists). A contributor doing a fresh clone and following the guide will hit `command not found`. The CLAUDE.md stack decision explicitly includes both tools.

**Fix:** Add a dev extras group to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.9",
    "mypy>=1.8",
    "pytest>=8.0",
    "pytest-cov>=5.0",
]
```
Update CONTRIBUTING.md install step to `pip install -e ".[dev]"`.

---

## Info

### IN-01: README terminal query example uses incorrect script path

**File:** `README.md:392`
**Issue:** The FAQ answer uses `python3 memo_engine.py search "query" --vault ~/memo-vault` (bare filename). All other README examples use the full path `~/.claude/skills/memo-skill/scripts/memo_engine.py`. The bare path only works if the user is already in the scripts/ directory, which is not an expected user workflow.

**Fix:**
```bash
python3 ~/.claude/skills/memo-skill/scripts/memo_engine.py search "query" --vault ~/memo-vault
```

### IN-02: CHANGELOG mentions MCP server but README install does not cover it

**File:** `CHANGELOG.md:26`
**Issue:** The changelog says "MCP server for Claude Desktop and Cursor integration" was added, but README has no section on MCP setup (how to install, configure, or use it). The optional dep `mcp[cli]` exists in pyproject.toml but is not explained anywhere in user-facing docs.

**Fix:** Add a brief "MCP Integration (optional)" section to README, or note it is coming in a future doc update. A CHANGELOG entry for a feature with zero documentation is a dead end for users.

### IN-03: CONTRIBUTING.md states no tests exist in v1.0.0

**File:** `CONTRIBUTING.md:30`
**Issue:** "No automated test suite in v1.0.0" is an honest disclosure but creates a quality signal problem — the project CLAUDE.md stack decision includes `pytest>=8.0` and `pytest-cov>=5.0`, indicating tests are intended. Shipping 1.0.0 with no tests and no test infrastructure in pyproject.toml is inconsistent with the project's own documented stack decisions.

**Fix:** Either add a placeholder `tests/` directory with a minimal smoke test so the test harness is wired, or change the version to `0.1.0` to signal pre-production state. A `0.x` version is a clearer signal that the project is not yet stable.

---

_Reviewed: 2026-04-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
