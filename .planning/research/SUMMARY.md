# Research Summary: claude-memo

**Date:** 2026-04-13
**Confidence:** HIGH

## Executive Summary

claude-memo — полностью рабочий, production-проверенный скилл для Claude Code. Инструмент уже превосходит конкурентов по глубине функционала (5 lifecycle-хуков, Obsidian-native вывод, кросс-проектная память, семантическая дедупликация). Milestone — не строить новые фичи, а взять рабочий личный инструмент и опубликовать как надёжный open-source проект.

Главный риск — необратимый: публикация персональных данных в git-историю. Второй риск — adoption friction: 1.1 GB silent download и молчащий first-run failure.

## Stack

- `pyproject.toml` + `uv_build >=0.11.6` — единый источник метаданных
- `uv >=0.5` — заменяет pip + venv + pip-tools
- `ruff >=0.9` — lint + format, заменяет flake8 + black + isort
- `mypy >=1.8` — стабильный type checker
- `pytest >=8.0` + `pytest-cov >=5.0` — тестирование
- GitHub Actions + `astral-sh/setup-uv@v5` + `bandit >=1.8` — CI pipeline
- `gitleaks >=8.21` — secret scanning
- **NOT PyPI** — скилл устанавливается через git clone в `~/.claude/skills/memo-skill/`

## Table Stakes (для публикации)

- README с value prop, install-шагами, примерами, стоимостью
- CONTRIBUTING.md
- Sensitive data audit (hard blocker)
- GitHub topics: `claude-code`, `memory`, `obsidian`, `mcp`

## Differentiators (уже есть)

- Obsidian-native vault (конкуренты хранят в SQLite/vector DBs)
- 5-hook lifecycle (SessionStart, Stop, PreCompact, SessionEnd, cron)
- Семантическая дедупликация
- Кросс-проектная память
- MCP server для Claude Desktop/Cursor
- Стоимость ~$0.002/session (прозрачно)

## Critical Pitfalls (confirmed via code inspection)

1. **Installed copy содержит реальные project names** — `memo_mcp_server.py` line 147: `jobhunter`, `digital-planet`. Публиковать ТОЛЬКО из clean copy (`~/Downloads/memo-skill/`)
2. **`~/engineering-brain` в 9 местах** — заменить на `~/memo-vault`
3. **README содержит реальные проекты** — `JobHunter.no`, `Finn.no` в примере note format
4. **Silent first-run failure** — `save_raw_log.py` молча падает без `MEMO_VAULT_PATH`
5. **1.1 GB model download без progress** — выглядит зависшим

## Suggested Phases (4)

1. **Security & Cleanliness** — sensitive data scan, replace `~/engineering-brain`, verify source dir. Hard blocker.
2. **Code Hardening** — pyproject.toml, ruff, mypy, pin deps, fix save_raw_log.py guard, model download progress
3. **Documentation & Trust** — README rewrite, CONTRIBUTING.md, CHANGELOG.md, examples/
4. **CI & Release** — GitHub Actions, issue templates, git tag v1.0.0, push public

## Out of Scope (this milestone)

- PyPI publication
- Homebrew formula
- Docker image
- Web UI
- Cloud sync

---
*Synthesized from: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md*
