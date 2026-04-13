# Phase 3: Documentation - Research

**Researched:** 2026-04-13
**Domain:** Open-source CLI tool documentation (README, CONTRIBUTING, CHANGELOG, examples/)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** README opens with value proposition and a concrete terminal demo (before/after showing knowledge persistence). Features list follows, then installation, then usage.
- **D-02:** Tone is developer-to-developer, direct, no marketing language. Target audience is Claude Code power users who want persistent memory.
- **D-03:** Include badges at top: CI status, Python version range (3.10+), license (MIT).
- **D-04:** Show real terminal output for key commands (search, save, warm-up) per DOC-01 requirement.
- **D-05:** Primary install path: `git clone` + `pip install -r requirements.txt`. This is the established flow.
- **D-06:** Mention `uv` as a faster alternative one-liner, but pip is the primary documented path.
- **D-07:** Installation section must be copy-paste complete: clone, install deps, init vault, warm-up model, configure hooks — no steps requiring external knowledge.
- **D-08:** `examples/` directory contains a single `hooks.json` — the ready-to-use hooks configuration for Claude Code.
- **D-09:** No additional example files beyond the hooks config.
- **D-10:** CONTRIBUTING.md — standard depth: dev setup, code style (ruff + mypy commands), PR process, issue guidelines.
- **D-11:** No architecture guide or deep technical docs in CONTRIBUTING.md.
- **D-12:** CHANGELOG.md — initial v1.0.0 entry in Keep a Changelog format (keepachangelog.com).

### Claude's Discretion

- Exact wording of README value proposition (as long as it's concrete and shows terminal output)
- Badge placement and formatting choices
- CHANGELOG entry categorization (Added/Changed/Fixed sections)
- Whether to include a "How it works" architecture section in README (short diagram is fine)
- Cost transparency section placement and detail level

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOC-01 | README rewritten for open-source audience — value prop first, copy-paste install, usage examples with real output, cost transparency | README structure patterns; existing README content audit; terminal output capture strategy |
| DOC-02 | CONTRIBUTING.md created — dev setup, PR process, code style, issue guidelines | Standard open-source CONTRIBUTING.md patterns; project tooling (ruff, mypy commands) |
| DOC-03 | CHANGELOG.md created — initial v1.0.0 entry | Keep a Changelog format standard |
| DOC-04 | `examples/` directory with hooks config JSON (copy-paste ready for new users) | Hooks JSON already in README; extraction path is clear |

</phase_requirements>

## Summary

This is a pure documentation phase — no code changes, only file creation and one file rewrite. The research task is to inventory what content already exists, identify what needs to be written from scratch, and establish the exact format standards for each deliverable.

The existing README.md is 15.4KB and comprehensive but poorly structured for a new user's decision process: features come before the value proposition demo, installation is incomplete (missing env var setup), and the hooks JSON belongs in `examples/` not inline. The rewrite is structural, not substantive — most content is reusable.

Three files need to be created from scratch: `CONTRIBUTING.md`, `CHANGELOG.md`, and `examples/hooks.json`. The hooks JSON config already exists verbatim in README.md and SKILL.md — it just needs extraction with minor updates (SKILL.md version uses `$MEMO_VAULT_PATH` in the SessionEnd command, which is the correct production form).

**Primary recommendation:** Treat this as a reorganization + gap-fill, not a rewrite from scratch. Extract existing content into the right structure, add the missing cost transparency and 1.1GB warning, write three new small files.

## Standard Stack

### Core (documentation tooling)
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Keep a Changelog | 1.1.0 format | CHANGELOG.md format | [CITED: keepachangelog.com] — the only widely-adopted standard for human-readable changelogs |
| Shields.io | — | README badges | [ASSUMED] Standard for open-source badges; used by 99% of GitHub projects |
| GitHub Flavored Markdown | — | All .md files | [VERIFIED: codebase] Project is on GitHub, all existing docs use GFM |

There is no package to install. This phase is entirely file creation/editing.

## Architecture Patterns

### Deliverable Map

```
claude-memo/
├── README.md          ← REWRITE (existing 15.4KB → restructured)
├── CONTRIBUTING.md    ← CREATE (new file, ~100 lines)
├── CHANGELOG.md       ← CREATE (new file, ~30 lines)
└── examples/
    └── hooks.json     ← CREATE (extracted from README/SKILL.md)
```

### README Structure (locked by D-01)

```
1. Title + one-line tagline
2. Badges (CI, Python 3.10+, MIT)
3. Value proposition paragraph (2-3 sentences)
4. Before/after terminal demo block
5. Features list (bullet points, scannable)
6. Requirements (upfront: Python 3.10+, ~1.1GB disk, ANTHROPIC_API_KEY)
7. Installation (copy-paste complete, 5 steps)
8. Configuration (env vars, hooks)
9. Usage (commands table + examples with real output)
10. Architecture diagram (optional, keep short)
11. Cost transparency (explicit: $0.002/session, $1/month at 5 sessions/day)
12. FAQ
13. Contributing (brief, points to CONTRIBUTING.md)
14. License
```

### CONTRIBUTING.md Structure (locked by D-10)

```
1. Development setup (git clone, pip install, test run)
2. Code style (ruff check ., ruff format ., mypy scripts/)
3. Running tests (if any exist; placeholder if not)
4. PR process (branch naming, what to include in PR)
5. Issue guidelines (bug reports vs feature requests)
```

### CHANGELOG.md Format (locked by D-12)

Keep a Changelog format: [CITED: keepachangelog.com]

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-13

### Added
- ...

[1.0.0]: https://github.com/your-user/claude-memo/releases/tag/v1.0.0
```

### Anti-Patterns to Avoid

- **Wall-of-text opening:** The existing README starts with three paragraphs before any code. New README must have terminal output visible before the scroll fold.
- **Incomplete install steps:** Current Quick Start omits `MEMO_VAULT_PATH` env var setup and the 1.1GB model download warning. Both are user-blocking surprises that must be prominent.
- **Hooks JSON inline only:** The current README has hooks JSON as a code block in the middle of the page. It belongs in `examples/hooks.json` AND should still be shown inline (best practice: show it, then say "or copy from `examples/hooks.json`").
- **Marketing language:** Phrases like "Every architecture decision, every debug breakthrough" (current README) should be replaced with concrete specifics.
- **Version mismatch in install path:** Current Quick Start uses `github.com/your-user/memo.git` and installs to `~/.claude/skills/memo-skill`. Final repo URL is `github.com/USERNAME/claude-memo`. The correct install path must be confirmed before writing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Changelog format | Custom format | Keep a Changelog 1.1.0 | Widely recognized; GitHub auto-parses releases |
| Badge URLs | Custom badge service | shields.io | Standard; cached by CDN; huge template library |

**Key insight:** Documentation format standards exist specifically so readers can parse them instantly. Non-standard formats create friction.

## Content Inventory: Existing README → New README

What can be reused verbatim or with minor edits:

| Section | Current Location | Reuse Decision |
|---------|-----------------|----------------|
| Features list | README.md lines 25-40 | Reuse as-is; move after demo |
| Architecture diagram (ASCII) | README.md lines 134-158 | Reuse; move to later section |
| Note format example | README.md lines 169-213 | Reuse |
| Auto-capture table | README.md lines 219-226 | Reuse |
| Commands table | README.md lines 119-131 | Reuse |
| FAQ | README.md lines 290-319 | Reuse with additions |
| Configuration env vars | README.md lines 278-288 | Reuse |
| Vault structure | README.md lines 233-251 | Reuse |
| Files table | README.md lines 336-349 | Reuse |
| Hooks JSON | README.md lines 60-94 | Extract to examples/hooks.json; keep inline reference |

What needs to be written new:

| Content | Why New | Notes |
|---------|---------|-------|
| Before/after terminal demo | Required by D-01/D-04 | Must show real-looking terminal output |
| 1.1GB download warning callout | Prominent gotcha | Currently buried in Requirements section |
| MEMO_VAULT_PATH env var step | Missing from install | Critical for hooks to work |
| Cost transparency section | DOC-01 explicit requirement | Scattered in FAQ currently; needs dedicated section |
| CONTRIBUTING.md (full file) | Does not exist | ~100 lines |
| CHANGELOG.md (full file) | Does not exist | ~30 lines |
| examples/hooks.json | Does not exist | Extract from README/SKILL.md |

## Common Pitfalls

### Pitfall 1: Install Path Inconsistency
**What goes wrong:** README, SKILL.md, and hooks JSON use different install paths. README uses `~/.claude/skills/memo-skill`, SKILL.md uses `~/.claude/skills/memo-skill/scripts/`, hooks JSON references same. If any path differs, hooks silently fail.
**Why it happens:** Multiple docs edited independently.
**How to avoid:** Set one canonical install path at the top of README installation section and reference it everywhere. Use `INSTALL_DIR=~/.claude/skills/memo-skill` as a named variable in the bash snippets.
**Warning signs:** Hook commands use different base paths in different sections.

### Pitfall 2: Hooks JSON Divergence Between README and examples/
**What goes wrong:** README inline hooks JSON and `examples/hooks.json` get out of sync over time, confusing users.
**Why it happens:** Two copies of the same content.
**How to avoid:** In README, show an abbreviated version and say "full config: see `examples/hooks.json`". Or show full config inline and note it's the same as the file. Choose one canonical approach and document it.

### Pitfall 3: Terminal Demo Shows Fake Output
**What goes wrong:** Planner creates a demo block with output that doesn't match actual script behavior.
**Why it happens:** Writing docs without running the tool.
**How to avoid:** Run actual commands to capture real output. For the before/after demo, the "before" scenario (Claude forgetting between sessions) is necessarily illustrative — that's acceptable as long as the "after" shows real search output format.

### Pitfall 4: Missing ANTHROPIC_API_KEY Setup in Install Steps
**What goes wrong:** User installs, runs warm-up, configures hooks — then auto-memo silently fails because API key isn't set.
**Why it happens:** API key is only mentioned in Requirements section and FAQ.
**How to avoid:** Install step 4 or 5 must explicitly say: "Set `ANTHROPIC_API_KEY` in your shell profile. Without it, auto-memo (Haiku classification) is disabled — manual `/memo` still works."

### Pitfall 5: v1.0.0 vs 0.1.0 Version Confusion
**What goes wrong:** pyproject.toml says `version = "0.1.0"` but CONTEXT.md and requirements say "v1.0.0 entry". CHANGELOG.md would be created for v1.0.0 but the package metadata says 0.1.0.
**Why it happens:** Version not synchronized between planning docs and code.
**How to avoid:** Planner must decide: bump pyproject.toml to 1.0.0 as part of this phase, or create CHANGELOG entry for 0.1.0. The CONTEXT.md D-12 says "v1.0.0 entry" — either the pyproject.toml needs to be updated to 1.0.0, or the CHANGELOG entry should be [0.1.0].
**Recommendation:** Planner should include a task to update pyproject.toml version to 1.0.0 if CHANGELOG is for v1.0.0. Alternatively, keep 0.1.0 everywhere and document it as such.

## Code Examples

### examples/hooks.json — Canonical Form

The correct production hooks config (from SKILL.md lines 84-118, which uses `$MEMO_VAULT_PATH` in SessionEnd — this is the correct form vs README which hardcodes `~/memo-vault`):

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/skills/memo-skill/scripts/session_context.py"
      }]
    }],
    "SessionEnd": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "bash ~/.claude/skills/memo-skill/scripts/auto_memo_hook.sh $MEMO_VAULT_PATH"
      }]
    }],
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/skills/memo-skill/scripts/pre_compact_save.py"
      }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/skills/memo-skill/scripts/should_suggest_memo.py",
        "timeout": 5
      }]
    }]
  }
}
```

[VERIFIED: codebase — SKILL.md lines 84-118]

Note: README currently uses `~/memo-vault` hardcoded in SessionEnd. SKILL.md uses `$MEMO_VAULT_PATH`. The env var form is correct — user configures the path once in their shell profile.

### README Badge Row

```markdown
![CI](https://github.com/USERNAME/claude-memo/actions/workflows/ci.yml/badge.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
```

[ASSUMED] — CI badge URL depends on Phase 4 workflow filename. Planner should use placeholder or note dependency.

### README Installation Block (complete 5-step form)

```bash
# Step 1: Clone
git clone https://github.com/USERNAME/claude-memo.git ~/.claude/skills/memo-skill

# Step 2: Install dependencies
cd ~/.claude/skills/memo-skill
pip install -r requirements.txt
# Alternative: uv pip install -r requirements.txt

# Step 3: Initialize vault
bash scripts/init_vault.sh ~/memo-vault

# Step 4: Download embedding model (~1.1GB, one-time, takes 2-5 minutes)
python3 scripts/memo_engine.py warm-up

# Step 5: Set up automation (cron reindex, git backup, model warm-up)
bash scripts/setup_automation.sh ~/memo-vault
```

Then set env var in shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export MEMO_VAULT_PATH=~/memo-vault
export ANTHROPIC_API_KEY=your-key-here  # Required for auto-memo
```

Then add hooks to Claude Code — copy `examples/hooks.json` content into `~/.claude/settings.json`.

[VERIFIED: codebase — scripts/ directory confirmed, SKILL.md setup steps]

### CONTRIBUTING.md Skeleton

```markdown
# Contributing to claude-memo

## Development Setup

git clone https://github.com/USERNAME/claude-memo.git
cd claude-memo
pip install -r requirements.txt

## Code Style

ruff check scripts/     # Lint
ruff format scripts/    # Format
mypy scripts/memo_engine.py scripts/auto_memo.py  # Type check

## Tests

(No automated tests in v1.0.0 — manual testing against a local vault)

## Pull Requests

1. Fork and create a branch: feature/your-feature or fix/your-fix
2. Make changes — keep commits focused
3. Ensure ruff and mypy pass
4. Open a PR with a clear description of what and why

## Issues

Bug report: include Python version, OS, error message, and steps to reproduce.
Feature request: describe the problem it solves, not just the solution.
```

### CHANGELOG.md v1.0.0 Entry Topics

Based on REQUIREMENTS.md completed features:

- SEC-01 through SEC-05: Clean, genericized codebase ready for public release
- CODE-01: pyproject.toml with project metadata and tool configs
- CODE-02: Pinned dependencies in requirements.txt
- CODE-03 through CODE-05: Explicit error handling, ruff config, mypy config
- DOC-01 through DOC-04: This phase's output (README, CONTRIBUTING, CHANGELOG, examples/)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` | `pyproject.toml` | PEP 621, 2021+ | Already done in Phase 2 |
| `CHANGES.txt` | `CHANGELOG.md` (Keep a Changelog) | ~2015 | Standard for human-readable logs |
| Inline-only hooks config | `examples/` directory | Emerging best practice | New users can copy without reading the full README |

**Deprecated/outdated:**
- Hardcoded `~/memo-vault` in hooks commands: replaced by `$MEMO_VAULT_PATH` env var (more flexible)

## Open Questions (RESOLVED)

1. **GitHub username / final repo URL**
   - RESOLVED: Use `USERNAME` placeholder in all URLs during this phase. Phase 4 (CI-04) fills in the real GitHub username.

2. **CHANGELOG version: 0.1.0 or 1.0.0?**
   - RESOLVED: Bump pyproject.toml to 1.0.0 to match CHANGELOG v1.0.0 entry (Plan 03-02, Task 3).

3. **CI badge dependency**
   - RESOLVED: Add badge speculatively with `USERNAME` placeholder. It activates after Phase 4 CI setup. Standard practice.

4. **MEMO_VAULT_PATH default behavior**
   - RESOLVED: Document that `init_vault.sh` creates `~/memo-vault`, and `MEMO_VAULT_PATH` env var is an optional override (Plan 03-01, Task 1 install section).

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — this phase creates only markdown and JSON files).

## Validation Architecture

Step 4: SKIPPED — no automated tests apply to documentation files. Success criteria are human-verifiable:
1. README opens with terminal demo before scroll fold (visual check)
2. Installation steps are copy-paste complete (walkthrough check)
3. `examples/hooks.json` is valid JSON (`python3 -m json.tool examples/hooks.json`)
4. CONTRIBUTING.md exists with all required sections
5. CHANGELOG.md follows Keep a Changelog format with v1.0.0 entry

The JSON validity check (`python3 -m json.tool`) is the only automated verification step.

## Security Domain

Not applicable for this phase — documentation files contain no executable code. The only security consideration is ensuring no personal data, API keys, or project-specific names appear in any created files (per SEC-01 through SEC-03, already completed in Phase 1 for existing files; new files must follow the same standard).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Shields.io is the standard badge service for GitHub READMEs | Standard Stack | Low — any badge service works; shields.io is overwhelmingly standard |
| A2 | CI badge URL format: `github.com/USERNAME/claude-memo/actions/workflows/ci.yml/badge.svg` | Code Examples | Medium — Phase 4 may use a different workflow filename than `ci.yml` |
| A3 | SKILL.md's `$MEMO_VAULT_PATH` form of SessionEnd command is the intended production form (vs README's hardcoded `~/memo-vault`) | Code Examples | Medium — if wrong, hooks.json ships with an incorrect command |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] README.md — full content audit completed
- [VERIFIED: codebase] SKILL.md — hooks config canonical form
- [VERIFIED: codebase] scripts/ directory listing — all 12 files confirmed
- [VERIFIED: codebase] pyproject.toml — version = "0.1.0", confirmed
- [VERIFIED: codebase] requirements.txt — dependencies confirmed
- [CITED: keepachangelog.com/en/1.1.0/] — CHANGELOG format standard

### Secondary (MEDIUM confidence)
- [CITED: context.md D-01 through D-12] — all locked decisions confirmed

### Tertiary (LOW confidence)
- [ASSUMED] Shields.io badge format — standard but not verified against current shields.io API

## Metadata

**Confidence breakdown:**
- Content inventory: HIGH — all files read directly from codebase
- Format standards (Keep a Changelog): HIGH — official spec cited
- Exact wording/demo content: MEDIUM — planner has discretion (D per CONTEXT.md)
- Badge URLs: LOW — depend on Phase 4 workflow filename and GitHub username

**Research date:** 2026-04-13
**Valid until:** 2026-05-13 (stable domain — documentation standards don't change)
