# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-13

### Added

- Persistent engineering memory vault with Obsidian-native markdown notes
- Semantic search via `intfloat/multilingual-e5-large` (1024 dims, 50+ languages)
- Keyword search via SQLite FTS5 index
- Automatic capture: SessionEnd hook classifies conversations via Claude Haiku
- Mid-session save: PreCompact hook preserves context before compression
- Smart context loading: SessionStart hook loads relevant notes into new sessions
- Decision nudge: Stop hook detects decision-making language and suggests `/memo`
- 10 slash commands: save, find, query, list, project, dedup, lint, stats, link, reindex
- Daily log compilation via cron (compile_logs.py)
- Vault health checks: broken links, orphans, empty notes, missing frontmatter
- Deduplication via semantic similarity threshold
- Race-safe writes via fcntl.flock file locking
- Git-backed vault with automated push via cron
- MCP server for Claude Desktop and Cursor integration
- Copy-paste hooks config in examples/hooks.json

### Changed

- Default vault path standardized to `~/memo-vault`
- All dependencies pinned in requirements.txt for reproducible installs

### Fixed

- Scripts now exit with explicit error when MEMO_VAULT_PATH is not set (instead of silent failure)
- Ruff and mypy pass cleanly on all modules

[1.0.0]: https://github.com/sergei-aronsen/claude-memo/releases/tag/v1.0.0
