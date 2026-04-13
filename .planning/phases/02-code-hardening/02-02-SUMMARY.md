---
phase: 02-code-hardening
plan: 02
subsystem: scripts
tags: [error-handling, vault-path, defensive-coding, CODE-03]
dependency_graph:
  requires: []
  provides: [explicit-vault-validation]
  affects: [scripts/save_raw_log.py, scripts/session_context.py, scripts/pre_compact_save.py]
tech_stack:
  added: []
  patterns: [three-condition vault path validation, stderr error + sys.exit(1)]
key_files:
  modified:
    - scripts/save_raw_log.py
    - scripts/session_context.py
    - scripts/pre_compact_save.py
decisions:
  - "Error message is identical across all three scripts per D-03/D-04"
  - "session_context.py previously used sys.exit(0) on missing vault (silent pass-through); now exits 1 with error"
  - "--vault arg parsing added to session_context.py and pre_compact_save.py (was already in save_raw_log.py)"
metrics:
  duration: 3min
  completed: 2026-04-13
  tasks_completed: 1
  files_modified: 3
---

# Phase 02 Plan 02: Vault Path Validation Summary

## One-liner

Explicit stderr + exit(1) validation when MEMO_VAULT_PATH unset and ~/memo-vault missing, replacing silent fallback in three hook scripts.

## What Was Built

Applied the three-condition vault path validation pattern (D-03) to `save_raw_log.py`, `session_context.py`, and `pre_compact_save.py`. All three scripts now:

1. Check `MEMO_VAULT_PATH` env var first
2. Fall back to `--vault` CLI argument if env var is unset
3. Check if `~/memo-vault` exists as a last resort
4. Print an explicit error to stderr and call `sys.exit(1)` if all three conditions fail

Previously, `save_raw_log.py` silently fell back to `~/memo-vault` even when that directory didn't exist, causing confusing downstream failures. `session_context.py` and `pre_compact_save.py` used `os.environ.get("MEMO_VAULT_PATH", os.path.expanduser("~/memo-vault"))` with no existence check.

`session_context.py` also previously called `sys.exit(0)` on missing vault (treated as a no-op hook), which masked configuration errors. It now correctly exits 1.

`--vault` argument parsing was added to `session_context.py` and `pre_compact_save.py` (it already existed in `save_raw_log.py`).

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Vault path validation for all three scripts | 171ad5a | scripts/save_raw_log.py, scripts/session_context.py, scripts/pre_compact_save.py |

## Verification

All three scripts tested with `env MEMO_VAULT_PATH="" HOME="/nonexistent"`:
- Error message printed to stderr: confirmed
- Exit code 1: confirmed
- Message identical across all three scripts: confirmed

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. The `os.path.exists()` check on the vault path mitigates T-02-02 (path traversal via user-controlled env var) as planned in the threat model.

## Self-Check: PASSED

- scripts/save_raw_log.py: exists, contains "MEMO_VAULT_PATH is not set", file=sys.stderr, sys.exit(1)
- scripts/session_context.py: exists, contains "MEMO_VAULT_PATH is not set", file=sys.stderr, sys.exit(1)
- scripts/pre_compact_save.py: exists, contains "MEMO_VAULT_PATH is not set", file=sys.stderr, sys.exit(1)
- Commit 171ad5a: exists
