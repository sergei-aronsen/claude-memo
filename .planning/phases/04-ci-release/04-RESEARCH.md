# Phase 4: CI & Release - Research

**Researched:** 2026-04-14
**Domain:** GitHub Actions CI, GitHub repository management, issue templates
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** GitHub username is `sergei-aronsen` — replace all USERNAME placeholders in README.md, CONTRIBUTING.md, CHANGELOG.md.
- **D-02:** Single workflow file `.github/workflows/ci.yml`.
- **D-03:** Triggers: `push` to main + `pull_request` to main.
- **D-04:** Matrix: Python 3.10, 3.11, 3.12 on ubuntu-latest.
- **D-05:** Steps: checkout → setup-python (with pip cache) → install deps → ruff check → mypy → bandit. All three must pass.
- **D-06:** Pin GitHub Actions to full SHA per CLAUDE.md. Set `permissions: contents: read`.
- **D-07:** Create repo via `gh repo create sergei-aronsen/claude-memo --public`.
- **D-08:** Description: "Persistent engineering memory for Claude Code — semantic search, automatic capture, Obsidian vault".
- **D-09:** Topics: `claude-code`, `memory`, `obsidian`, `mcp`.
- **D-10:** No branch protection rules at v1.0.0.
- **D-11:** Default branch: `main`.
- **D-12:** Issue templates in `.github/ISSUE_TEMPLATE/`: bug_report.md and feature_request.md.
- **D-13:** Bug report fields: description, steps to reproduce, expected vs actual, environment. Feature request fields: description, use case, alternatives considered.
- **D-14:** Create repo via `gh`, add remote origin, push main branch.
- **D-15:** Replace all USERNAME placeholders BEFORE push.

### Claude's Discretion

- Exact CI step names and job naming
- Issue template formatting details beyond required fields
- Whether to add `.github/FUNDING.yml` or other optional files
- Exact bandit configuration (which checks to run/skip)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CI-01 | GitHub Actions: lint (ruff) + type check (mypy) + test (pytest) on push/PR | Workflow YAML pattern confirmed; no pytest yet per codebase state — CI-01 text says "test" but no test suite exists; bandit covers security per CI-02 |
| CI-02 | Security scanning in CI — bandit for Python security issues | bandit 1.9.4 confirmed current; install via pip in CI step |
| CI-03 | Multi-Python matrix: 3.10, 3.11, 3.12 | actions/setup-python v5 matrix strategy confirmed |
| CI-04 | GitHub repo `claude-memo` created public with description and topics | `gh repo create` + `gh repo edit --add-topic` pattern confirmed |
| CI-05 | Issue templates: bug report + feature request | `.github/ISSUE_TEMPLATE/` markdown template pattern confirmed |
| CI-06 | Code pushed to GitHub, repo live and accessible | git remote add + push pattern; gh auth confirmed as sergei-aronsen |
</phase_requirements>

---

## Summary

Phase 4 is primarily a DevOps/configuration phase — it involves creating GitHub infrastructure (repo, CI workflow, issue templates) and replacing placeholders in documentation. The technical complexity is low-to-medium: the Python toolchain (ruff, mypy, bandit) is already configured in `pyproject.toml` from Phase 2, so the CI workflow just orchestrates calls to these existing tools.

The main decisions are already locked: single workflow file, pip-based install (not uv, since no `uv.lock` exists), Python 3.10/3.11/3.12 matrix, SHA-pinned actions. The only non-trivial research finding is that `bandit` is NOT in `requirements.txt` — CI must install it explicitly as a dev tool.

The repo does not exist yet on GitHub (`gh repo view sergei-aronsen/claude-memo` returned NOT EXISTS). The `gh` CLI is authenticated as `sergei-aronsen` with `repo` and `workflow` scopes — sufficient for repo creation and pushing workflows.

**Primary recommendation:** Create `.github/` directory structure first (workflow + templates), replace USERNAME placeholders, then create GitHub repo and push — so the CI badge in README resolves immediately after the push.

## Standard Stack

### Core Actions (SHA-pinned per CLAUDE.md)

| Action | Tag | SHA | Purpose |
|--------|-----|-----|---------|
| `actions/checkout` | v4.2.2 | `11bd71901bbe5b1630ceea73d27597364c9af683` | Checkout repo in CI |
| `actions/setup-python` | v5.4.0 | `42375524e23c412d93fb67b49958b491fce71c38` | Install Python + pip cache |

[VERIFIED: GitHub API `gh api repos/actions/checkout/git/ref/tags/v4.2.2` and `gh api repos/actions/setup-python/git/ref/tags/v5.4.0`]

### Python Tools in CI

| Tool | Version | Install Command | Purpose |
|------|---------|----------------|---------|
| `ruff` | pinned in requirements.txt | `pip install ruff` (or from requirements) | Lint + format check |
| `mypy` | pinned in requirements.txt | via requirements.txt | Type checking |
| `bandit` | 1.9.4 (latest as of 2026-02-25) | `pip install bandit` (NOT in requirements.txt) | Security scanning |

[VERIFIED: bandit 1.9.4 confirmed via pypi.org/project/bandit/]
[VERIFIED: bandit not in requirements.txt — confirmed by reading file]

**Critical gap:** `bandit` is not in `requirements.txt`. CI must install it via a separate `pip install bandit` step. Per D-06 in CONTEXT.md and CLAUDE.md stack recommendations, bandit `>=1.8` is the target — installing without a pin is acceptable for CI (gets latest), or pin to `bandit==1.9.4`.

### GitHub CLI Commands

| Task | Command |
|------|---------|
| Create repo | `gh repo create sergei-aronsen/claude-memo --public --description "..."` |
| Add topics | `gh repo edit sergei-aronsen/claude-memo --add-topic claude-code --add-topic memory --add-topic obsidian --add-topic mcp` |
| Add remote | `git remote add origin https://github.com/sergei-aronsen/claude-memo.git` |
| Push | `git push -u origin main` |

[VERIFIED: `gh repo edit --add-topic` confirmed via GitHub CLI docs discussion at github.com/cli/cli/discussions/4376]
[VERIFIED: `gh auth status` confirms logged in as `sergei-aronsen` with `repo` + `workflow` scopes]

## Architecture Patterns

### Workflow Structure

```
.github/
├── workflows/
│   └── ci.yml            # Single CI workflow
└── ISSUE_TEMPLATE/
    ├── bug_report.md
    └── feature_request.md
```

### Pattern 1: Single-job CI with Matrix

Since there are no tests, a single job with a matrix covers all three tools across all Python versions. This is simpler than separate parallel jobs and produces one clear pass/fail per Python version.

```yaml
# Source: GitHub Actions docs / verified pattern
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    name: CI (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38  # v5.4.0
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Install dev tools
        run: pip install bandit==1.9.4

      - name: Lint (ruff)
        run: ruff check scripts/

      - name: Format check (ruff)
        run: ruff format --check scripts/

      - name: Type check (mypy)
        run: mypy scripts/memo_engine.py scripts/auto_memo.py

      - name: Security scan (bandit)
        run: bandit -r scripts/ -ll
```

[VERIFIED: `actions/setup-python` `cache: pip` with `cache-dependency-path` confirmed via official docs]
[VERIFIED: SHA values confirmed via GitHub API]
[ASSUMED: `bandit -r scripts/ -ll` flags — `-r` for recursive, `-ll` to report medium/high severity only. Low severity noise is common in Python code; `-ll` is a common CI convention. Confirm or adjust based on actual bandit output.]

### Pattern 2: Issue Template (GitHub markdown format)

```markdown
---
name: Bug report
about: Something is not working as expected
title: ''
labels: bug
assignees: ''
---

## Description
<!-- What happened? -->

## Steps to Reproduce
1. 
2. 

## Expected Behavior
<!-- What should have happened? -->

## Actual Behavior
<!-- What actually happened? -->

## Environment
- Python version: 
- OS: 
- Claude Code version: 
```

[ASSUMED: Label `bug` will auto-create on first use in GitHub — no pre-creation needed]

### Anti-Patterns to Avoid

- **Tag-based action pins:** `uses: actions/checkout@v4` is NOT pinned — a compromised tag can point to malicious code. ALWAYS use full SHA. CLAUDE.md mandates this.
- **`pip install -r requirements.txt` without pip cache:** Cold installs of sentence-transformers take 30-60 seconds on every run. The `cache: pip` key in setup-python makes this fast.
- **Running bandit on all files including docs:** Use `bandit -r scripts/` not `bandit -r .` to avoid false positives from non-Python directories.
- **Pushing before creating GitHub repo:** `git push` will fail if the remote doesn't exist. Repo creation must precede the push.
- **Adding topics via `gh repo create`:** The `--topic` flag behavior varies by gh version; `gh repo edit --add-topic` is the reliable method post-creation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pip dependency caching | Custom cache step | `cache: pip` in setup-python | Built-in, uses requirements.txt hash as key automatically |
| SHA lookup for action pins | Manual lookup | `gh api repos/OWNER/REPO/git/ref/tags/TAG --jq '.object.sha'` | Authoritative, fast, verified |
| Topic setting | GitHub web UI | `gh repo edit --add-topic` | Scriptable, repeatable |

## Common Pitfalls

### Pitfall 1: bandit Low-Severity Noise

**What goes wrong:** Running `bandit -r scripts/` without severity filter produces dozens of B101 (assert_used) and B603 (subprocess) warnings that are not real vulnerabilities in this codebase, causing CI to fail.

**Why it happens:** Bandit's default threshold is LOW severity. The codebase uses `assert` statements (legitimate Python) and subprocess calls in shell scripts.

**How to avoid:** Use `-ll` flag (medium and high only) or `-l` (high only) in CI. The project's Python scripts use `assert` for type narrowing (confirmed in Phase 2 decisions).

**Warning signs:** CI run shows 10+ bandit issues on the first run — most will be B101.

### Pitfall 2: mypy "scripts" path configuration

**What goes wrong:** Running `mypy scripts/` scans all 10 Python files, but only `memo_engine.py` and `auto_memo.py` have type annotations (per Phase 2 D-07). Other scripts will produce many errors.

**Why it happens:** Phase 2 only added mypy config for two files, not the full scripts/ directory.

**How to avoid:** Run `mypy scripts/memo_engine.py scripts/auto_memo.py` explicitly, matching the Phase 2 D-07 decision. Alternatively, add `exclude` patterns to `pyproject.toml [tool.mypy]`.

**Warning signs:** mypy error count jumps from ~0 to 50+ if all scripts are scanned.

### Pitfall 3: Python version string quoting in matrix

**What goes wrong:** `python-version: [3.10, 3.11, 3.12]` — YAML parses `3.10` as float `3.1`, which becomes Python `3.1` (not found).

**Why it happens:** YAML float parsing.

**How to avoid:** Always quote Python versions: `["3.10", "3.11", "3.12"]`.

**Warning signs:** Error "Unable to find python version spec 3.1" on first CI run.

### Pitfall 4: USERNAME placeholder in CI badge

**What goes wrong:** If USERNAME in README.md is not replaced before push, the CI badge on the repo homepage shows a broken image.

**Why it happens:** The badge URL `https://github.com/USERNAME/claude-memo/actions/...` is rendered on the GitHub repo page.

**How to avoid:** D-15 mandates replacement before push. Verify with `grep -r "USERNAME" README.md CONTRIBUTING.md CHANGELOG.md` before committing the push.

**Warning signs:** Broken image icon next to "CI" on the GitHub repo page.

### Pitfall 5: `workflow` token scope required for pushing workflow files

**What goes wrong:** `git push` of `.github/workflows/ci.yml` fails with "refusing to allow" error even though the repo exists.

**Why it happens:** GitHub requires the `workflow` OAuth scope to push files in `.github/workflows/`. Regular `repo` scope is not sufficient.

**How to avoid:** Confirmed: `gh auth status` shows `sergei-aronsen` has `workflow` scope — no action needed. [VERIFIED: confirmed via `gh auth status` output]

## Code Examples

### Complete ci.yml

```yaml
# Source: Actions SHA verified via GitHub API; structure per D-02 through D-06
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    name: CI (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38  # v5.4.0
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Install dev tools
        run: pip install bandit==1.9.4

      - name: Lint (ruff)
        run: ruff check scripts/

      - name: Format check (ruff)
        run: ruff format --check scripts/

      - name: Type check (mypy)
        run: mypy scripts/memo_engine.py scripts/auto_memo.py

      - name: Security scan (bandit)
        run: bandit -r scripts/ -ll
```

### Repository creation sequence

```bash
# Step 1: Create repo (repo does not exist yet - verified)
gh repo create sergei-aronsen/claude-memo \
  --public \
  --description "Persistent engineering memory for Claude Code — semantic search, automatic capture, Obsidian vault"

# Step 2: Add topics (must be done separately - gh repo create has no --topic flag)
gh repo edit sergei-aronsen/claude-memo \
  --add-topic claude-code \
  --add-topic memory \
  --add-topic obsidian \
  --add-topic mcp

# Step 3: Add remote and push
git remote add origin https://github.com/sergei-aronsen/claude-memo.git
git push -u origin main
```

### USERNAME replacement

```bash
# Files with USERNAME placeholders (verified by grep):
# README.md: lines 5, 67
# CONTRIBUTING.md: line 6
# CHANGELOG.md: line 38

# Replacement pattern (use Edit tool per CLAUDE.md):
# Replace: USERNAME
# With: sergei-aronsen
```

### Bug report template

```markdown
---
name: Bug report
about: Something is not working as expected
title: '[BUG] '
labels: bug
assignees: ''
---

## Description

<!-- Clear description of what went wrong -->

## Steps to Reproduce

1. 
2. 
3. 

## Expected Behavior

<!-- What should have happened -->

## Actual Behavior

<!-- What actually happened — include error messages if any -->

## Environment

- Python version: 
- OS: 
- Claude Code version (from `claude --version`): 
- Installation method: git clone
```

### Feature request template

```markdown
---
name: Feature request
about: Suggest an improvement or new capability
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Description

<!-- Clear description of the feature -->

## Use Case

<!-- What problem does this solve? How would you use it? -->

## Alternatives Considered

<!-- What workarounds or alternatives have you tried? -->

## Additional Context

<!-- Screenshots, examples, or related issues -->
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gh` CLI | Repo creation, topic setting | ✓ | (confirmed) | GitHub web UI |
| `git` | Push to remote | ✓ | (system) | — |
| `sergei-aronsen` GitHub auth | Repo creation + push | ✓ | active account | — |
| `workflow` OAuth scope | Pushing ci.yml | ✓ | confirmed in token scopes | — |
| `repo` OAuth scope | Repo creation, topics | ✓ | confirmed in token scopes | — |
| `bandit` | CI only (not local) | ✗ locally | — | Not needed locally; installed in CI |

[VERIFIED: `gh auth status` output confirms all scopes and active account]
[VERIFIED: `gh repo view sergei-aronsen/claude-memo` returned NOT EXISTS — repo creation is needed]

**Missing dependencies with no fallback:** None — all required tools are available.

## Validation Architecture

> workflow.nyquist_validation not explicitly set — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None — no test suite exists (deferred to v2 per REQUIREMENTS.md TEST-01/02/03) |
| Config file | None |
| Quick run command | N/A |
| Full suite command | N/A |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-01 | CI workflow triggers on push/PR | manual — verify GitHub Actions tab | Check GitHub Actions tab after push | N/A |
| CI-02 | Bandit runs and passes in CI | manual — CI run result | Check GitHub Actions tab after push | N/A |
| CI-03 | Matrix runs for 3.10, 3.11, 3.12 | manual — CI matrix results | Check 3 matrix rows in GitHub Actions | N/A |
| CI-04 | Repo visible at correct URL with topics | manual — `gh repo view` | `gh repo view sergei-aronsen/claude-memo` | N/A |
| CI-05 | Issue templates appear in GitHub UI | manual — check New Issue button | Browse to github.com/sergei-aronsen/claude-memo/issues/new/choose | N/A |
| CI-06 | Repo accessible, README renders | manual — browser check | `gh repo view --web` | N/A |

**Note:** Phase 4 is entirely infrastructure/config. All verification is manual (check GitHub UI/API after push). There is no code logic to unit test.

### Wave 0 Gaps

None — no test infrastructure needed for this phase.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | no | N/A |
| V6 Cryptography | no | N/A |

This phase adds no application code — it is pure CI/repo configuration. The relevant security controls are the CLAUDE.md CI/CD rules:

| CLAUDE.md Rule | Applied How |
|---------------|-------------|
| Pin Actions to full SHA | ci.yml uses `@SHA # tag` format |
| `permissions: contents: read` | Top-level permissions block in ci.yml |
| No secrets in repo files | ci.yml uses no secrets; no credentials needed for public repo |
| No `workflow` token escalation | Job has no `id-token: write` or broader scopes |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `bandit -r scripts/ -ll` will pass with no medium/high issues in the codebase | Code Examples (ci.yml) | CI fails on first run; need to adjust severity flag or add `# nosec` comments |
| A2 | `ruff format --check scripts/` will pass (code was formatted in Phase 2) | Code Examples (ci.yml) | CI fails; need a `ruff format scripts/` run before push |
| A3 | `mypy scripts/memo_engine.py scripts/auto_memo.py` will pass (Phase 2 hardening) | Code Examples (ci.yml) | CI fails; may need mypy fixes before push |
| A4 | Issue template labels (`bug`, `enhancement`) auto-create on first use | Code Examples (templates) | Low risk — GitHub creates labels automatically |
| A5 | `fail-fast: false` is preferred over default `true` for matrix | Code Examples (ci.yml) | If `true`: one Python version failure cancels others; less diagnostic info |

## Open Questions (RESOLVED)

1. **Will bandit pass on the current scripts/ directory?**
   - RESOLVED: Plan 04-01 includes bandit in CI. Run locally before push to catch issues early. If failures appear, fix code or add targeted `# nosec` comments. Documented as Assumption A1.

2. **Should ruff format check be included in CI?**
   - RESOLVED: Yes — Plan 04-01 Task 2 includes `ruff format --check scripts/` as a CI step. Run `ruff format scripts/` locally before push to ensure clean state.

## Sources

### Primary (HIGH confidence)
- GitHub API — `gh api repos/actions/checkout/git/ref/tags/v4.2.2` — SHA `11bd71901bbe5b1630ceea73d27597364c9af683` [VERIFIED]
- GitHub API — `gh api repos/actions/setup-python/git/ref/tags/v5.4.0` — SHA `42375524e23c412d93fb67b49958b491fce71c38` [VERIFIED]
- `gh auth status` — confirms `sergei-aronsen` active with `repo` + `workflow` scopes [VERIFIED]
- `gh repo view sergei-aronsen/claude-memo` — repo does NOT exist yet [VERIFIED]
- `requirements.txt` in repo — bandit NOT present [VERIFIED]
- `pyproject.toml` — ruff and mypy already configured [VERIFIED]

### Secondary (MEDIUM confidence)
- [pypi.org/project/bandit/](https://pypi.org/project/bandit/) — bandit 1.9.4, released 2026-02-25, Python >=3.10 [CITED]
- [github.com/cli/cli/discussions/4376](https://github.com/cli/cli/discussions/4376) — `gh repo edit --add-topic` is the correct command for adding topics [CITED]
- [github.com/actions/setup-python](https://github.com/actions/setup-python) — `cache: pip` with `cache-dependency-path` confirmed [CITED]

### Tertiary (LOW confidence)
- `-ll` flag for bandit severity filtering — from documentation and community patterns [ASSUMED — validate with local run]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions and SHAs verified via GitHub API and PyPI
- Architecture: HIGH — workflow pattern is standard; locked decisions from CONTEXT.md leave little ambiguity
- Pitfalls: HIGH — most verified from codebase inspection (bandit not in requirements.txt, mypy scope, USERNAME placeholders)

**Research date:** 2026-04-14
**Valid until:** 2026-05-14 (Actions SHA pins remain valid until upstream tags move)
