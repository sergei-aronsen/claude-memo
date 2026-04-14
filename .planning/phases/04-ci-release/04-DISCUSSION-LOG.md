# Phase 4: CI & Release - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-14
**Phase:** 04-ci-release
**Areas discussed:** CI Workflow Design, Repo Creation & Configuration, Issue Templates, Push Strategy
**Mode:** --auto (all decisions auto-selected)

---

## CI Workflow Design

| Option | Description | Selected |
|--------|-------------|----------|
| Single ci.yml | One workflow file with matrix — simple for small project | ✓ |
| Separate workflows | lint.yml, typecheck.yml, security.yml — more granular status checks | |

**User's choice:** [auto] Single ci.yml (recommended — project is small)

| Option | Description | Selected |
|--------|-------------|----------|
| push + pull_request | Standard open-source triggers | ✓ |
| pull_request only | Only CI on PRs | |
| push + PR + schedule | Add weekly scheduled run | |

**User's choice:** [auto] push to main + pull_request (recommended — standard)

---

## Repo Creation & Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| sergei-aronsen | Detected from gh auth status | ✓ |

**User's choice:** [auto] sergei-aronsen (detected automatically)

| Option | Description | Selected |
|--------|-------------|----------|
| No branch protection | Single maintainer, less friction | ✓ |
| Basic protection | Require PR reviews | |

**User's choice:** [auto] No branch protection (recommended for v1.0.0 single-maintainer)

---

## Issue Templates

| Option | Description | Selected |
|--------|-------------|----------|
| Standard markdown | .github/ISSUE_TEMPLATE/ with bug_report.md + feature_request.md | ✓ |
| YAML forms | Structured issue forms with dropdowns | |
| Minimal | Single ISSUE_TEMPLATE.md | |

**User's choice:** [auto] Standard markdown (recommended — per CI-05)

---

## Push Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| gh create + push main | Create repo via gh CLI, add remote, push | ✓ |
| Manual GitHub creation | Create via web UI first | |

**User's choice:** [auto] gh create + push main (recommended — automated, clean)

---

## Claude's Discretion

- CI step names and job naming
- Issue template formatting details
- Optional GitHub config files (FUNDING.yml etc)
- Bandit configuration specifics

## Deferred Ideas

None
