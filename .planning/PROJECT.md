# Memo (claude-memo)

## What This Is

Persistent engineering memory for Claude Code. Builds an Obsidian vault with semantic search, automatic capture, and cross-project intelligence. Every architecture decision, debug breakthrough, and hard-won pattern is captured automatically and searchable by meaning — across sessions, across projects.

## Core Value

Knowledge survives between sessions. What you learned today is available tomorrow — automatically, without manual effort.

## Requirements

### Validated

- ✓ Semantic search via multilingual-e5-large (local, 50+ languages) — existing
- ✓ Auto-capture via SessionEnd hook (Haiku classification, ~$0.002/session) — existing
- ✓ Smart context loading via SessionStart hook — existing
- ✓ Mid-session nudges via Stop hook (keyword heuristic, $0) — existing
- ✓ PreCompact hook saves context before compression — existing
- ✓ Obsidian-native vault (markdown + YAML frontmatter + wikilinks) — existing
- ✓ Semantic deduplication before save — existing
- ✓ Cross-project intelligence (one vault, tags + wikilinks) — existing
- ✓ Race-safe writes via fcntl.flock — existing
- ✓ SQLite + FTS5 keyword search — existing
- ✓ Daily log compilation via cron — existing
- ✓ Terminal query mode (memo_engine.py query) — existing
- ✓ Vault health checks (/memo lint) — existing
- ✓ MCP server for Claude Desktop/Cursor — existing

### Active

- [ ] Publish to GitHub as `claude-memo` (public repo)
- [x] README доведён до open-source уровня (installation, contributing, examples) — Validated in Phase 3: Documentation
- [x] Проверка на отсутствие чувствительных данных в коде — Validated in Phase 1: Security & Cleanliness
- [x] Code hardening: pyproject.toml, pinned deps, ruff/mypy, defensive error handling — Validated in Phase 2: Code Hardening

### Out of Scope

- Mobile app — vault is plain markdown, доступен через любой редактор
- Web UI — Obsidian покрывает визуализацию
- Cloud sync — git push по cron уже работает
- Поддержка других AI-ассистентов (Copilot, Cursor native) — фокус на Claude Code, MCP покрывает Claude Desktop/Cursor

## Context

- Код полностью написан и работает в production (установлен на машине автора)
- Стек: Python 3.10+, sentence-transformers, SQLite + FTS5, intfloat/multilingual-e5-large
- Чистая копия кода лежит в `~/Downloads/memo-skill/` (без личных данных)
- Установленная копия: `~/.claude/skills/memo-skill/` (может содержать project-specific примеры)
- Автор только начал использовать — дальнейшее развитие итеративно по мере наблюдений
- Инструкции по публикации: `~/Downloads/MEMO_GITHUB_PUBLISH.md`

## Constraints

- **Sensitive data**: Перед публикацией обязательна проверка на отсутствие личных данных, API-ключей, project-specific имён
- **Source of truth**: Чистый zip (`~/Downloads/memo-skill/`), не установленная копия
- **Repo name**: `claude-memo` на GitHub
- **License**: MIT (уже есть)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GitHub repo name: `claude-memo` | Привязка к Claude Code в названии, узнаваемо | — Pending |
| Публикация из чистого zip, не из installed copy | Installed copy может содержать personal project names | — Pending |
| Итеративное развитие после публикации | Код свежий, нужно наблюдение перед планированием фич | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after Phase 3 completion*
