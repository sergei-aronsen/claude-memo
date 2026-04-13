---
phase: 2
slug: code-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | ruff (linter) + mypy (type checker) — no pytest tests in this phase |
| **Config file** | pyproject.toml (created in this phase) |
| **Quick run command** | `ruff check scripts/` |
| **Full suite command** | `ruff check scripts/ && mypy scripts/memo_engine.py scripts/auto_memo.py` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `ruff check scripts/`
- **After every plan wave:** Run `ruff check scripts/ && mypy scripts/memo_engine.py scripts/auto_memo.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CODE-01 | — | N/A | config | `test -f pyproject.toml` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CODE-02 | — | N/A | config | `pip install -r requirements.txt --dry-run` | ✅ | ⬜ pending |
| 02-02-01 | 02 | 1 | CODE-03 | — | N/A | integration | `MEMO_VAULT_PATH= python scripts/save_raw_log.py < /dev/null 2>&1; echo $?` | ✅ | ⬜ pending |
| 02-03-01 | 03 | 2 | CODE-04 | — | N/A | lint | `ruff check scripts/` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | CODE-05 | — | N/A | typecheck | `mypy scripts/memo_engine.py scripts/auto_memo.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — ruff + mypy tool configs (created as part of CODE-01)
- [ ] `pip install ruff mypy` — tools not currently installed

*Wave 0 is effectively Plan 01 (packaging setup) which enables all subsequent verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| requirements.txt reproducibility | CODE-02 | Needs clean venv to verify | `python -m venv /tmp/test-env && /tmp/test-env/bin/pip install -r requirements.txt` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
