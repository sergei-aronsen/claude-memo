---
phase: 4
slug: ci-release
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + gh CLI |
| **Config file** | none |
| **Quick run command** | `gh repo view sergei-aronsen/claude-memo --json name,description,topics 2>/dev/null` |
| **Full suite command** | `ruff check scripts/ && mypy scripts/memo_engine.py scripts/auto_memo.py && bandit -r scripts/ -ll` |
| **Estimated runtime** | ~10 seconds (local), ~2 min (CI) |

---

## Sampling Rate

- **After every task commit:** Verify files created/modified as expected
- **After every plan wave:** Run full suite command locally
- **Before `/gsd-verify-work`:** CI must have passed on GitHub
- **Max feedback latency:** 120 seconds (CI run)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CI-01,CI-02,CI-03 | — | Actions pinned to SHA | manual | `test -f .github/workflows/ci.yml` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | CI-05 | — | N/A | manual | `test -f .github/ISSUE_TEMPLATE/bug_report.md && test -f .github/ISSUE_TEMPLATE/feature_request.md` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | CI-04 | — | N/A | manual | `gh repo view sergei-aronsen/claude-memo` | ❌ | ⬜ pending |
| 04-02-02 | 02 | 2 | CI-06 | — | No secrets in push | manual | `gh api repos/sergei-aronsen/claude-memo/actions/runs --jq '.workflow_runs[0].status'` | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*No test framework needed. Phase uses gh CLI and file existence checks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI runs on push/PR | CI-01 | Requires GitHub infra | Push to repo, check Actions tab shows running workflow |
| Matrix shows 3 Python versions | CI-03 | Requires GitHub infra | Check Actions run has 3 matrix jobs (3.10, 3.11, 3.12) |
| Repo publicly accessible | CI-04 | Requires browser/API | Visit github.com/sergei-aronsen/claude-memo in incognito |
| Topics correct | CI-04 | Requires repo to exist | `gh repo view --json topics` shows all 4 topics |
| Clone + install works | CI-06 | End-to-end test | Clone from GitHub URL, follow README install steps |

---

## Acceptance Criteria Tracing

| Requirement | Success Criterion | Automated? |
|-------------|-------------------|------------|
| CI-01 | CI workflow runs ruff + mypy + bandit on push/PR | Partial (file exists check) |
| CI-02 | bandit passes in CI | No (requires CI run) |
| CI-03 | Matrix: Python 3.10, 3.11, 3.12 | No (requires CI run) |
| CI-04 | Repo public with description and topics | `gh repo view` |
| CI-05 | Bug report + feature request templates | File existence check |
| CI-06 | Code pushed, repo live | `gh repo view` + clone test |
