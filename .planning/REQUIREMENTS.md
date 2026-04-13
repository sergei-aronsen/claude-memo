# Requirements: claude-memo

**Defined:** 2026-04-13
**Core Value:** Knowledge survives between sessions — automatically, without manual effort.

## v1 Requirements

Requirements for open-source publication. Each maps to roadmap phases.

### Security & Cleanliness

- [x] **SEC-01**: Clean copy scanned for sensitive data (personal names, API keys, project-specific references) — zero findings
- [x] **SEC-02**: Default vault path replaced from `~/engineering-brain` to `~/memo-vault` across all scripts (9 occurrences)
- [x] **SEC-03**: README examples genericized — no real project names (JobHunter.no, Finn.no, Webcruiter, Jobbnorge removed)
- [x] **SEC-04**: `.gitignore` verified to exclude `.memo/` directory (index.db, embeddings.npy, write.lock, auto_memo.log)
- [x] **SEC-05**: Published repo uses single-commit workflow (no leaked history from personal development)

### Code Hardening

- [ ] **CODE-01**: `pyproject.toml` created with project metadata, dependencies, and tool configs (ruff, mypy)
- [ ] **CODE-02**: Dependency versions pinned in requirements.txt (sentence-transformers, anthropic, etc.)
- [ ] **CODE-03**: `save_raw_log.py` fails with explicit stderr message when `MEMO_VAULT_PATH` not set (instead of silent failure)
- [ ] **CODE-04**: ruff configuration added — lint + format rules for consistent code style
- [ ] **CODE-05**: mypy configuration added — type checking for critical modules

### Documentation

- [ ] **DOC-01**: README rewritten for open-source audience — value prop first, copy-paste install, usage examples with real output, cost transparency
- [ ] **DOC-02**: CONTRIBUTING.md created — dev setup, PR process, code style, issue guidelines
- [ ] **DOC-03**: CHANGELOG.md created — initial v1.0.0 entry
- [ ] **DOC-04**: `examples/` directory with hooks config JSON (copy-paste ready for new users)

### CI & Release

- [ ] **CI-01**: GitHub Actions workflow — lint (ruff) + type check (mypy) + test (pytest) on push/PR
- [ ] **CI-02**: Security scanning in CI — bandit for Python security issues
- [ ] **CI-03**: Multi-Python matrix — 3.10, 3.11, 3.12
- [ ] **CI-04**: GitHub repo `claude-memo` created (public) with description and topics
- [ ] **CI-05**: Issue templates — bug report + feature request
- [ ] **CI-06**: Code pushed to GitHub, repo live and accessible

## v2 Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Packaging

- **PKG-01**: PyPI publication (`pip install claude-memo`)
- **PKG-02**: Homebrew formula

### UX Improvements

- **UX-01**: Progress bar for 1.1GB model download (warm-up command)
- **UX-02**: Pre-commit hooks config for contributors (.pre-commit-config.yaml)

### Testing

- **TEST-01**: Test suite for memo_engine.py core functions
- **TEST-02**: Integration tests for hook scripts
- **TEST-03**: Coverage target 60%+

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Docker image | Overkill for a Claude Code skill — git clone is simpler |
| Web UI | Obsidian covers visualization; vault is plain markdown |
| Cloud sync service | Git push cron already handles backup |
| Mobile app | Vault accessible via any markdown editor |
| Support for non-Claude AI assistants | Focus on Claude Code; MCP covers Claude Desktop/Cursor |
| Restructuring to src/ layout | Breaks `~/.claude/skills/` path conventions that hooks depend on |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| SEC-03 | Phase 1 | Complete |
| SEC-04 | Phase 1 | Complete |
| SEC-05 | Phase 1 | Complete |
| CODE-01 | Phase 2 | Pending |
| CODE-02 | Phase 2 | Pending |
| CODE-03 | Phase 2 | Pending |
| CODE-04 | Phase 2 | Pending |
| CODE-05 | Phase 2 | Pending |
| DOC-01 | Phase 3 | Pending |
| DOC-02 | Phase 3 | Pending |
| DOC-03 | Phase 3 | Pending |
| DOC-04 | Phase 3 | Pending |
| CI-01 | Phase 4 | Pending |
| CI-02 | Phase 4 | Pending |
| CI-03 | Phase 4 | Pending |
| CI-04 | Phase 4 | Pending |
| CI-05 | Phase 4 | Pending |
| CI-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after roadmap creation*
