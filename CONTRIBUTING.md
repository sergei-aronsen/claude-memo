# Contributing to claude-memo

## Development Setup

```bash
git clone https://github.com/sergei-aronsen/claude-memo.git
cd claude-memo
pip install -r requirements.txt
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking.

```bash
# Lint
ruff check scripts/

# Format
ruff format scripts/

# Type check
mypy scripts/memo_engine.py scripts/auto_memo.py
```

All checks must pass before submitting a PR.

## Tests

No automated test suite in v1.0.0. Testing is done manually against a local vault:

```bash
# Initialize a test vault
bash scripts/init_vault.sh /tmp/test-vault

# Run warm-up
python3 scripts/memo_engine.py warm-up

# Test search
python3 scripts/memo_engine.py search "test query" --vault /tmp/test-vault
```

## Pull Requests

1. Fork the repo and create a branch: `feature/your-feature` or `fix/your-fix`
2. Make your changes — keep commits focused and descriptive
3. Ensure `ruff check scripts/` and `ruff format --check scripts/` pass
4. Ensure `mypy scripts/memo_engine.py scripts/auto_memo.py` passes
5. Open a PR with a clear description of what changed and why

## Issues

**Bug reports** — include: Python version, OS, full error message, and steps to reproduce.

**Feature requests** — describe the problem it solves, not just the solution you want.

## Design Principles

- The Obsidian vault (markdown files) is the source of truth. The index is always derived and rebuildable.
- No external services required (except optional Haiku for auto-memo).
- Everything must work for a single developer with 5 notes or 5,000.
