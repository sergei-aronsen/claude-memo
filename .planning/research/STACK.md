# Technology Stack — Open Source Publishing

**Project:** claude-memo
**Milestone:** GitHub open-source publication
**Researched:** 2026-04-13
**Overall confidence:** HIGH (verified against official docs and 2025/2026 sources)

---

## Context

The tool already works in production. This is NOT a greenfield stack decision — it's about what's needed to take an existing Python 3.10+, sentence-transformers, SQLite project from a local install to a publicly publishable open-source repository.

The code lives in `~/Downloads/memo-skill/` as a flat scripts directory (`scripts/*.py`, `scripts/*.sh`), with a `requirements.txt` and a `LICENSE`. No `pyproject.toml`, no tests, no CI, no package structure.

The goal: ship a clean, installable, trustworthy open-source project without over-engineering it.

---

## Recommended Stack

### Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pyproject.toml` | PEP 621 (no version) | Single source of project metadata | Standard since Python 3.11, replaces `setup.py` + `setup.cfg`. Every modern tool reads it. |
| `uv_build` | `>=0.11.6,<0.12` | Build backend | Native uv backend — zero extra deps, integrates with uv toolchain. Suitable for pure-Python projects (which this is). |
| `uv` | `>=0.5` | Developer workflow (install, sync, build, publish) | Fastest Python toolchain available. Replaces pip + venv + pip-tools in one binary. `uv sync --frozen` in CI runs in seconds. |

**NOT recommended:**
- `Poetry` — adds cognitive overhead, slower, has broken lock files in the past. uv supersedes its workflow.
- `setuptools` — legacy. Still works but requires more config for nothing extra.
- `Hatchling` — good alternative to uv_build, but unnecessary if using uv throughout. Only switch to it if you need dynamic version from git tags.

**pyproject.toml skeleton for this project:**

```toml
[build-system]
requires = ["uv_build>=0.11.6,<0.12"]
build-backend = "uv_build"

[project]
name = "claude-memo"
version = "0.1.0"
description = "Persistent engineering memory for Claude Code"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "sentence-transformers>=2.2.0",
    "numpy>=1.24.0",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
mcp = ["mcp[cli]>=1.2.0"]

[project.scripts]
memo = "claude_memo.cli:main"
```

Note: `memo_mcp_server.py` should be optional (`[project.optional-dependencies]`), not required — MCP dependency pulls in Pydantic, FastAPI internals, etc. Users who only want CLI shouldn't pay that cost.

**Confidence: HIGH** — verified against official uv docs (https://docs.astral.sh/uv/concepts/build-backend/)

---

### Linting and Formatting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `ruff` | `>=0.9` | Linting + formatting (replaces flake8 + black + isort) | 180M monthly PyPI downloads. Used by FastAPI, pandas, Hugging Face. Rust-speed — entire codebase in milliseconds. Single config in `pyproject.toml`. |

**NOT recommended:**
- `black` + `flake8` + `isort` separately — ruff replaces all three. No reason to maintain three tools.
- `pylint` — too verbose, too many false positives for a project this size.

**Confidence: HIGH** — ruff is the de facto standard as of 2025.

---

### Type Checking

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `mypy` | `>=1.8` | Static type checking | Still the most stable type checker. Wide CI integration. `ty` (Astral's new checker) is in preview as of early 2026 — not yet production-stable enough to bet on. |

**Watch:** `ty` (https://github.com/astral-sh/ty) — same team as ruff/uv, designed to replace mypy. Once it exits preview, switch. Expected to dominate by late 2026.

**Confidence: MEDIUM** — mypy is verified stable; ty is confirmed preview-only as of April 2026 per search results.

---

### Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pytest` | `>=8.0` | Test runner | Universal standard. Excellent fixture system for mocking CLI tools, filesystem ops, and subprocess calls. |
| `pytest-cov` | `>=5.0` | Coverage measurement | Integrates coverage.py into pytest runs. Generates XML for CI badges and reports. |

**Test scope for this project:**
- Unit tests for `memo_engine.py` (search, similarity, dedup logic) — pure Python, easy to mock SQLite.
- Integration tests for hook scripts calling `auto_memo.py` — mock Anthropic API with `responses` or `pytest-httpx`.
- No need for end-to-end tests at v0.1 — too much infra (Obsidian vault, cron).

**Coverage target:** 60%+ for MVP. Cover the semantic search core and dedup logic. Skip shell script wrapping.

**NOT recommended:**
- `unittest` — verbose, inferior fixtures. pytest is the standard.
- `tox` — adds abstraction without value for a single-maintainer project. Use GitHub Actions matrix directly.

**Confidence: HIGH**

---

### CI/CD

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GitHub Actions | — | CI pipeline | Already on GitHub. Native integration, free for public repos. |
| `astral-sh/setup-uv` | `v5` | uv in CI | Official action, handles caching via `uv.lock` hash. Installs uv + Python in one step. |
| `bandit` | `>=1.8` | Security scanning | Detects common Python vulnerabilities (hardcoded secrets in code, dangerous `subprocess` patterns). Fast, CI-friendly. |

**Recommended CI workflow structure:**

```
.github/workflows/ci.yml
  Triggers: push to main, PR to main
  Jobs (all on ubuntu-latest, Python 3.11 and 3.12):
    1. lint    — ruff check + ruff format --check
    2. type    — mypy scripts/
    3. test    — pytest --cov --cov-report=xml
    4. security — bandit -r scripts/
```

Matrix over Python 3.10, 3.11, 3.12 — the declared `requires-python = ">=3.10"` creates an obligation to verify compatibility.

**Release workflow:** Manual trigger or tag push → `uv build` + `uv publish` to PyPI. Keep simple at v0.1.

**NOT recommended:**
- Publishing to PyPI at v0.1 — the project installs via git clone + setup script. PyPI makes sense after the API stabilizes. Add it as a future milestone.
- `codecov.io` — requires account setup. Use GitHub Actions artifact upload of `coverage.xml` for now; add codecov when external contributors appear.

**Confidence: HIGH** — verified against https://ber2.github.io/posts/2025_github_actions_python/

---

### Documentation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `README.md` (plain markdown) | — | Primary docs | For a CLI tool with a narrow audience (Claude Code users), a comprehensive README is more useful than a docs site. Users want copy-paste install commands, not navigation. |

**README structure for this project:**

```
1. One-liner description + demo screenshot/GIF
2. Badges: Python version, license, CI status
3. How it works (2-3 paragraphs, no jargon)
4. Prerequisites (Python 3.10+, Claude Code, Obsidian)
5. Installation (step-by-step, copy-paste ready)
6. Usage (query mode, hook behavior)
7. Configuration reference
8. Contributing (link to CONTRIBUTING.md)
9. License
```

**Additional files:**
- `CONTRIBUTING.md` — dev setup, how to run tests, PR process
- `CHANGELOG.md` — start with `0.1.0` entry
- `.github/ISSUE_TEMPLATE/bug_report.md` — reduces noise in issues

**NOT recommended:**
- `MkDocs` or `Sphinx` — massive overkill for a tool with 5 public-facing commands. A well-written README beats a docs site for CLI tools in niche audiences.
- Auto-generated API docs — this is not a library. The "API" is the CLI.

**Confidence: HIGH**

---

### Secret Scanning (Pre-Publication)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `gitleaks` | `>=8.21` | Git history audit before going public | Fastest scanner, 24K+ GitHub stars, written in Go. Scans entire git history in seconds. Catches API keys, tokens, passwords. |
| `detect-secrets` | `>=1.5` | Baseline for ongoing prevention | Pre-commit hook integration. Creates a `.secrets.baseline` file — new contributors can't accidentally commit secrets. |

**Pre-publication workflow:**
1. Run `gitleaks detect --source . --log-opts="--all"` on the clean copy (`~/Downloads/memo-skill/`)
2. Review any findings — given the project has no git history yet in the clean copy, this is mostly a codebase scan
3. Add `detect-secrets` as a pre-commit hook going forward

**Confidence: HIGH** — gitleaks is confirmed best-in-class for pre-publish scans per 2025/2026 comparisons.

---

### Pre-commit Hooks

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pre-commit` | `>=4.0` | Hook management | Standard framework. Runs ruff, detect-secrets, and trailing-whitespace checks locally before every commit. Keeps CI green without surprises. |

**`.pre-commit-config.yaml` hooks:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.x
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

**Confidence: HIGH**

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build backend | `uv_build` | `hatchling` | Both are good; uv_build is zero-config if already using uv. Use hatchling only if dynamic versioning from git tags is needed. |
| Type checker | `mypy` | `ty` (Astral) | ty is in preview as of April 2026. Revisit in 6 months. |
| Formatter | `ruff format` | `black` | ruff format is black-compatible and removes a separate dependency. |
| Docs | README.md | MkDocs | Docs site is premature for a single-maintainer CLI tool with a niche audience. |
| Release automation | Manual | `python-semantic-release` | Unnecessary complexity at v0.1. Manual CHANGELOG + git tag is sufficient until there are contributors. |
| Secret scanner | `gitleaks` | `trufflehog` | TruffleHog's killer feature (credential verification) is irrelevant for pre-publish audit. Gitleaks is faster and simpler. |
| Package registry | Skip for now | PyPI | The install flow is `git clone + pip install -r requirements.txt`. PyPI makes sense after restructuring as a proper package with entry points. |

---

## Installation (Developer Setup)

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up
git clone https://github.com/yourusername/claude-memo
cd claude-memo
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run mypy scripts/

# Scan for secrets before publishing
brew install gitleaks
gitleaks detect --source . --log-opts="--all"
```

---

## Sources

- uv build backend docs: https://docs.astral.sh/uv/concepts/build-backend/
- uv projects guide: https://docs.astral.sh/uv/guides/projects/
- GitHub Actions Python 2025 setup: https://ber2.github.io/posts/2025_github_actions_python/
- Python packaging best practices 2026: https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/
- Python build backends comparison 2025: https://medium.com/@dynamicy/python-build-backends-in-2025-what-to-use-and-why-uv_build-vs-hatchling-vs-poetry-core-94dd6b92248f
- Secret scanning tools comparison 2025: https://www.jit.io/resources/appsec-tools/trufflehog-vs-gitleaks-a-detailed-comparison-of-secret-scanning-tools
- Python packaging user guide (official): https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- pyOpenSci README guidelines: https://www.pyopensci.org/python-package-guide/documentation/repository-files/readme-file-best-practices.html
