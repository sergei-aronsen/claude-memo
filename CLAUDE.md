<!-- GSD:project-start source:PROJECT.md -->
## Project

**Memo (claude-memo)**

Persistent engineering memory for Claude Code. Builds an Obsidian vault with semantic search, automatic capture, and cross-project intelligence. Every architecture decision, debug breakthrough, and hard-won pattern is captured automatically and searchable by meaning — across sessions, across projects.

**Core Value:** Knowledge survives between sessions. What you learned today is available tomorrow — automatically, without manual effort.

### Constraints

- **Sensitive data**: Перед публикацией обязательна проверка на отсутствие личных данных, API-ключей, project-specific имён
- **Source of truth**: Чистый zip (`~/Downloads/memo-skill/`), не установленная копия
- **Repo name**: `claude-memo` на GitHub
- **License**: MIT (уже есть)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Context
## Recommended Stack
### Packaging
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pyproject.toml` | PEP 621 (no version) | Single source of project metadata | Standard since Python 3.11, replaces `setup.py` + `setup.cfg`. Every modern tool reads it. |
| `uv_build` | `>=0.11.6,<0.12` | Build backend | Native uv backend — zero extra deps, integrates with uv toolchain. Suitable for pure-Python projects (which this is). |
| `uv` | `>=0.5` | Developer workflow (install, sync, build, publish) | Fastest Python toolchain available. Replaces pip + venv + pip-tools in one binary. `uv sync --frozen` in CI runs in seconds. |
- `Poetry` — adds cognitive overhead, slower, has broken lock files in the past. uv supersedes its workflow.
- `setuptools` — legacy. Still works but requires more config for nothing extra.
- `Hatchling` — good alternative to uv_build, but unnecessary if using uv throughout. Only switch to it if you need dynamic version from git tags.
### Linting and Formatting
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `ruff` | `>=0.9` | Linting + formatting (replaces flake8 + black + isort) | 180M monthly PyPI downloads. Used by FastAPI, pandas, Hugging Face. Rust-speed — entire codebase in milliseconds. Single config in `pyproject.toml`. |
- `black` + `flake8` + `isort` separately — ruff replaces all three. No reason to maintain three tools.
- `pylint` — too verbose, too many false positives for a project this size.
### Type Checking
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `mypy` | `>=1.8` | Static type checking | Still the most stable type checker. Wide CI integration. `ty` (Astral's new checker) is in preview as of early 2026 — not yet production-stable enough to bet on. |
### Testing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pytest` | `>=8.0` | Test runner | Universal standard. Excellent fixture system for mocking CLI tools, filesystem ops, and subprocess calls. |
| `pytest-cov` | `>=5.0` | Coverage measurement | Integrates coverage.py into pytest runs. Generates XML for CI badges and reports. |
- Unit tests for `memo_engine.py` (search, similarity, dedup logic) — pure Python, easy to mock SQLite.
- Integration tests for hook scripts calling `auto_memo.py` — mock Anthropic API with `responses` or `pytest-httpx`.
- No need for end-to-end tests at v0.1 — too much infra (Obsidian vault, cron).
- `unittest` — verbose, inferior fixtures. pytest is the standard.
- `tox` — adds abstraction without value for a single-maintainer project. Use GitHub Actions matrix directly.
### CI/CD
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GitHub Actions | — | CI pipeline | Already on GitHub. Native integration, free for public repos. |
| `astral-sh/setup-uv` | `v5` | uv in CI | Official action, handles caching via `uv.lock` hash. Installs uv + Python in one step. |
| `bandit` | `>=1.8` | Security scanning | Detects common Python vulnerabilities (hardcoded secrets in code, dangerous `subprocess` patterns). Fast, CI-friendly. |
- Publishing to PyPI at v0.1 — the project installs via git clone + setup script. PyPI makes sense after the API stabilizes. Add it as a future milestone.
- `codecov.io` — requires account setup. Use GitHub Actions artifact upload of `coverage.xml` for now; add codecov when external contributors appear.
### Documentation
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `README.md` (plain markdown) | — | Primary docs | For a CLI tool with a narrow audience (Claude Code users), a comprehensive README is more useful than a docs site. Users want copy-paste install commands, not navigation. |
- `CONTRIBUTING.md` — dev setup, how to run tests, PR process
- `CHANGELOG.md` — start with `0.1.0` entry
- `.github/ISSUE_TEMPLATE/bug_report.md` — reduces noise in issues
- `MkDocs` or `Sphinx` — massive overkill for a tool with 5 public-facing commands. A well-written README beats a docs site for CLI tools in niche audiences.
- Auto-generated API docs — this is not a library. The "API" is the CLI.
### Secret Scanning (Pre-Publication)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `gitleaks` | `>=8.21` | Git history audit before going public | Fastest scanner, 24K+ GitHub stars, written in Go. Scans entire git history in seconds. Catches API keys, tokens, passwords. |
| `detect-secrets` | `>=1.5` | Baseline for ongoing prevention | Pre-commit hook integration. Creates a `.secrets.baseline` file — new contributors can't accidentally commit secrets. |
### Pre-commit Hooks
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pre-commit` | `>=4.0` | Hook management | Standard framework. Runs ruff, detect-secrets, and trailing-whitespace checks locally before every commit. Keeps CI green without surprises. |
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
## Installation (Developer Setup)
# Install uv (if not installed)
# Clone and set up
# Run tests
# Run linter
# Run type checker
# Scan for secrets before publishing
## Sources
- uv build backend docs: https://docs.astral.sh/uv/concepts/build-backend/
- uv projects guide: https://docs.astral.sh/uv/guides/projects/
- GitHub Actions Python 2025 setup: https://ber2.github.io/posts/2025_github_actions_python/
- Python packaging best practices 2026: https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/
- Python build backends comparison 2025: https://medium.com/@dynamicy/python-build-backends-in-2025-what-to-use-and-why-uv_build-vs-hatchling-vs-poetry-core-94dd6b92248f
- Secret scanning tools comparison 2025: https://www.jit.io/resources/appsec-tools/trufflehog-vs-gitleaks-a-detailed-comparison-of-secret-scanning-tools
- Python packaging user guide (official): https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- pyOpenSci README guidelines: https://www.pyopensci.org/python-package-guide/documentation/repository-files/readme-file-best-practices.html
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
