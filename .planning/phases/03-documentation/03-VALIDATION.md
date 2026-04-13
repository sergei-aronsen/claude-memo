---
phase: 3
slug: documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + json.tool |
| **Config file** | none |
| **Quick run command** | `python3 -m json.tool examples/hooks.json` |
| **Full suite command** | `python3 -m json.tool examples/hooks.json && test -f CONTRIBUTING.md && test -f CHANGELOG.md` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m json.tool examples/hooks.json` (when hooks.json exists)
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | DOC-01 | — | No personal data in README | manual | `grep -r 'sergeiarutiunian\|sk-or-v1\|sk-ant-api\|jobhunter\|digital-planet' README.md` exits 1 | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | DOC-04 | — | Valid JSON config | unit | `python3 -m json.tool examples/hooks.json` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | DOC-02 | — | N/A | manual | `test -f CONTRIBUTING.md` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | DOC-03 | — | N/A | manual | `test -f CHANGELOG.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. No test framework needed — documentation phase uses file existence checks and JSON validation only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README value prop visible within 60s scan | DOC-01 | Subjective reading speed | Open README.md, timer: can you understand what this does and decide yes/no in 60 seconds? |
| Installation copy-paste complete | DOC-01 | Requires running commands on a clean system | Follow install steps on a fresh machine/venv — no step should require external knowledge |
| Real terminal output in examples | DOC-01 | Content fidelity check | Compare README examples to actual command output |
| CONTRIBUTING sections complete | DOC-02 | Content review | Verify: dev setup, code style, PR process, issue guidelines sections present |
| CHANGELOG follows Keep a Changelog | DOC-03 | Format review | Check against keepachangelog.com/en/1.1.0/ spec |

---

## Acceptance Criteria Tracing

| Requirement | Success Criterion | Automated? |
|-------------|-------------------|------------|
| DOC-01 | README value prop + real terminal output + copy-paste install | Partial (grep for sections) |
| DOC-02 | CONTRIBUTING.md with dev setup, code style, PR process | `test -f CONTRIBUTING.md` |
| DOC-03 | CHANGELOG.md with v1.0.0 entry | `test -f CHANGELOG.md && grep -q '1.0.0' CHANGELOG.md` |
| DOC-04 | examples/ with hooks config JSON | `python3 -m json.tool examples/hooks.json` |
