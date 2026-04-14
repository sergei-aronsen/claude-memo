# Phase 4: CI & Release - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up GitHub Actions CI pipeline, create the public `claude-memo` repository on GitHub under `sergei-aronsen`, configure repo metadata (topics, description), add issue templates, replace USERNAME placeholders, and push all code live.

</domain>

<decisions>
## Implementation Decisions

### GitHub Account
- **D-01:** GitHub username is `sergei-aronsen` (confirmed via `gh auth status`). All USERNAME placeholders across README.md, CONTRIBUTING.md, CHANGELOG.md get replaced with this value.

### CI Workflow
- **D-02:** Single workflow file `.github/workflows/ci.yml` — project is small, one file keeps it simple.
- **D-03:** Triggers: `push` to main branch + `pull_request` to main. Standard for open-source.
- **D-04:** Matrix: Python 3.10, 3.11, 3.12 on ubuntu-latest (per CI-01, CI-03).
- **D-05:** Steps: checkout → setup-python (with pip cache) → install deps → ruff check → mypy → bandit. All three tools must pass (per CI-01, CI-02).
- **D-06:** Pin GitHub Actions to full SHA per CLAUDE.md CI/CD security rules. Set `permissions: contents: read`.

### Repository Configuration
- **D-07:** Create repo via `gh repo create sergei-aronsen/claude-memo --public` with description and topics.
- **D-08:** Description: "Persistent engineering memory for Claude Code — semantic search, automatic capture, Obsidian vault"
- **D-09:** Topics: `claude-code`, `memory`, `obsidian`, `mcp` (per CI-04 success criteria).
- **D-10:** No branch protection rules at v1.0.0 — single-maintainer project, adds friction without value.
- **D-11:** Default branch: `main`.

### Issue Templates
- **D-12:** Standard GitHub markdown issue templates in `.github/ISSUE_TEMPLATE/`: bug_report.md and feature_request.md (per CI-05).
- **D-13:** Bug report includes: description, steps to reproduce, expected vs actual, environment (Python version, OS). Feature request includes: description, use case, alternatives considered.

### Push Strategy
- **D-14:** Create repo via `gh`, add remote origin, push main branch. Single push of all existing commits.
- **D-15:** Replace all USERNAME placeholders BEFORE push (README, CONTRIBUTING, CHANGELOG badge URLs and links).

### Claude's Discretion
- Exact CI step names and job naming
- Issue template formatting details beyond required fields
- Whether to add a `.github/FUNDING.yml` or other optional GitHub config files
- Exact bandit configuration (which checks to run/skip)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — CI-01 through CI-06 are the binding requirements
- `.planning/ROADMAP.md` — Phase 4 success criteria define what "done" means

### Security Rules
- `CLAUDE.md` — CI/CD Security section: pin actions to SHA, minimal permissions, no secrets in repo files

### Prior Phase Decisions
- `.planning/phases/03-documentation/03-CONTEXT.md` — README structure decisions, hooks.json location
- `.planning/phases/02-code-hardening/02-CONTEXT.md` — ruff/mypy config in pyproject.toml, Python 3.10+ target

### Files with USERNAME placeholders
- `README.md` — badge URLs, clone URL
- `CONTRIBUTING.md` — repo URL references
- `CHANGELOG.md` — release tag URL

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml` — Already has `[tool.ruff]` and `[tool.mypy]` sections configured (Phase 2)
- `requirements.txt` — Pinned dependencies ready for CI install
- `.gitignore` — Already configured for the project

### Established Patterns
- ruff check + ruff format commands (from CONTRIBUTING.md)
- mypy on scripts/memo_engine.py and scripts/auto_memo.py (from Phase 2 D-07)
- No test suite yet (deferred to v2 per REQUIREMENTS.md)

### Integration Points
- `.github/workflows/ci.yml` — new file
- `.github/ISSUE_TEMPLATE/bug_report.md` — new file
- `.github/ISSUE_TEMPLATE/feature_request.md` — new file
- README.md, CONTRIBUTING.md, CHANGELOG.md — USERNAME placeholder replacement
- Git remote origin — needs to be added

</code_context>

<specifics>
## Specific Ideas

- `gh auth status` confirms logged in as `sergei-aronsen` — repo creation can be automated via `gh repo create`
- No git remote exists yet — `git remote add origin` needed before push
- CI badge in README already uses placeholder format `github.com/USERNAME/claude-memo/actions/workflows/ci.yml/badge.svg` — just needs USERNAME→sergei-aronsen
- bandit is listed in CLAUDE.md tech stack but NOT in requirements.txt — CI must `pip install bandit` separately or add to dev deps

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-ci-release*
*Context gathered: 2026-04-14*
