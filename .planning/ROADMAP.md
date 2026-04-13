# Roadmap: claude-memo

## Overview

Working production tool transformed into a trustworthy open-source project. Four phases follow a natural dependency chain: security first (irreversible risk), code quality and docs in parallel (both block CI), then CI/release as the final delivery gate.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Security & Cleanliness** - Audit and sanitize source before any git history is created (completed 2026-04-13)
- [ ] **Phase 2: Code Hardening** - Add project metadata, tooling config, and defensive error handling
- [ ] **Phase 3: Documentation** - Write open-source-grade README, CONTRIBUTING.md, CHANGELOG, and examples
- [ ] **Phase 4: CI & Release** - Wire GitHub Actions, create repo, push live

## Phase Details

### Phase 1: Security & Cleanliness
**Goal**: Clean copy is provably free of sensitive data and ready to publish without leaking personal information
**Depends on**: Nothing (first phase)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05
**Success Criteria** (what must be TRUE):
  1. Automated scan of clean copy (`~/Downloads/memo-skill/`) reports zero findings for personal names, API keys, and project-specific references
  2. All 9 occurrences of `~/engineering-brain` are replaced with `~/memo-vault` and the vault path works in installation instructions
  3. README examples contain no real company or project names (JobHunter.no, Finn.no, Webcruiter, Jobbnorge are gone)
  4. `.gitignore` explicitly excludes `.memo/` directory contents (index.db, embeddings.npy, write.lock, auto_memo.log)
  5. Repo will be initialized with a single clean commit — no personal development history exposed
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Copy source files from clean zip into repo
- [x] 01-02-PLAN.md — Fix .gitignore, bulk-replace engineering-brain, update LICENSE
- [x] 01-03-PLAN.md — Sanitize README example names + human review
- [x] 01-04-PLAN.md — Comprehensive scan gate + single clean git commit

### Phase 2: Code Hardening
**Goal**: Project has standard Python packaging, consistent code style, type safety, and no silent failure modes
**Depends on**: Phase 1
**Requirements**: CODE-01, CODE-02, CODE-03, CODE-04, CODE-05
**Success Criteria** (what must be TRUE):
  1. `pyproject.toml` exists with project metadata, all dependencies, and tool configs (ruff + mypy sections)
  2. `requirements.txt` has pinned versions — `pip install -r requirements.txt` produces a reproducible environment
  3. Running `save_raw_log.py` without `MEMO_VAULT_PATH` set prints an explicit error to stderr and exits non-zero instead of failing silently
  4. `ruff check .` passes with zero errors on the codebase
  5. `mypy` passes on critical modules with zero errors
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Create pyproject.toml with metadata and tool configs, pin requirements.txt
- [ ] 02-02-PLAN.md — Add explicit vault path validation to entry-point scripts
- [ ] 02-03-PLAN.md — Install ruff/mypy, fix all lint and type errors

### Phase 3: Documentation
**Goal**: A new user can understand what claude-memo does, install it, and start using it from the README alone
**Depends on**: Phase 2
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):
  1. README opens with a concrete value proposition and shows real terminal output in examples — a developer can decide "yes/no" within 60 seconds
  2. README installation section is copy-paste complete: clone, configure hooks, run warm-up — no steps requiring external knowledge
  3. CONTRIBUTING.md exists with dev setup, code style instructions, and PR process
  4. CHANGELOG.md exists with a v1.0.0 entry describing initial features
  5. `examples/` directory contains a ready-to-use hooks config JSON that new users can copy directly into their Claude Code settings
**Plans**: TBD

### Phase 4: CI & Release
**Goal**: Public GitHub repo is live, CI passes, and the project is discoverable and contribution-ready
**Depends on**: Phase 3
**Requirements**: CI-01, CI-02, CI-03, CI-04, CI-05, CI-06
**Success Criteria** (what must be TRUE):
  1. GitHub Actions CI runs on every push/PR: lint (ruff) + type check (mypy) + security scan (bandit) pass across Python 3.10, 3.11, 3.12
  2. `github.com/[user]/claude-memo` is accessible publicly with correct description and topics (`claude-code`, `memory`, `obsidian`, `mcp`)
  3. Repository has bug report and feature request issue templates
  4. All code is pushed and the repo is live — a visitor can clone and install from the README instructions
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Security & Cleanliness | 4/4 | Complete   | 2026-04-13 |
| 2. Code Hardening | 0/3 | Not started | - |
| 3. Documentation | 0/? | Not started | - |
| 4. CI & Release | 0/? | Not started | - |
