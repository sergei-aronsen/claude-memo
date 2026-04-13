---
phase: 02-code-hardening
plan: 01
subsystem: packaging
tags: [pyproject, dependencies, ruff, mypy, packaging]
dependency_graph:
  requires: []
  provides: [pyproject.toml, pinned-requirements]
  affects: [ruff-linting, mypy-type-checking, reproducible-installs]
tech_stack:
  added: []
  patterns: [PEP-621-metadata-only, pinned-dependencies]
key_files:
  created: [pyproject.toml]
  modified: [requirements.txt]
decisions:
  - "pyproject.toml is metadata-only (no [build-system]) per D-01 — project installs via git clone + pip, not as a package"
  - "requirements.txt uses == pins (not >=) per D-02 for reproducible installs"
  - "ruff line-length=120, rules E/F/W/I selected per D-05/D-06"
  - "mypy not strict — ignore_missing_imports=true per D-07/D-08 for third-party libs without stubs"
metrics:
  duration: 64s
  completed_date: "2026-04-13"
  tasks_completed: 2
  files_changed: 2
---

# Phase 02 Plan 01: pyproject.toml and Pinned Dependencies Summary

**One-liner:** pyproject.toml with PEP 621 metadata + ruff/mypy tool configs; all 4 requirements.txt deps pinned with == instead of >=.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create pyproject.toml with metadata and tool configs | f25232f | pyproject.toml (created) |
| 2 | Pin dependency versions in requirements.txt | 84531e0 | requirements.txt (modified) |

## What Was Built

**pyproject.toml** — new file at repo root with:
- `[project]` table: name=claude-memo, version=0.1.0, description, readme, license=MIT, requires-python=>=3.10, keywords, core dependencies, optional mcp dependency
- `[tool.ruff]` with line-length=120, target-version=py310, select=E/F/W/I, per-file-ignores for two scripts with bare except
- `[tool.mypy]` with python_version=3.10, mypy_path=scripts, ignore_missing_imports=true, warn_unused_ignores=true
- No `[build-system]` table — intentional, project is not a pip-installable package

**requirements.txt** — all 4 dependencies updated from >= ranges to exact == pins:
- sentence-transformers: >=2.2.0 → ==5.4.0
- numpy: >=1.24.0 → ==2.4.4
- PyYAML: >=6.0 → ==6.0.3
- mcp[cli]: >=1.2.0 → ==1.27.0

## Verification

- `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"` — exits 0
- No `>=` ranges in requirements.txt — confirmed via Python
- No `[build-system]` section in pyproject.toml — confirmed

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — pyproject.toml and requirements.txt are static config files with no network endpoints, auth paths, or user input handling.

## Self-Check: PASSED

- pyproject.toml exists: FOUND
- requirements.txt updated: FOUND
- Commit f25232f exists: FOUND
- Commit 84531e0 exists: FOUND
