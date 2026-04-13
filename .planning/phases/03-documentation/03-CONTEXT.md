# Phase 3: Documentation - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Write open-source-grade documentation so a new user can independently evaluate, install, and start using claude-memo from the README alone. Deliverables: rewritten README, CONTRIBUTING.md, CHANGELOG.md, and an examples/ directory with a copy-paste hooks config.

</domain>

<decisions>
## Implementation Decisions

### README Structure & Voice
- **D-01:** README opens with value proposition and a concrete terminal demo (before/after showing knowledge persistence). Features list follows, then installation, then usage. This matches DOC-01: "value prop first".
- **D-02:** Tone is developer-to-developer, direct, no marketing language. Target audience is Claude Code power users who want persistent memory.
- **D-03:** Include badges at top: CI status, Python version range (3.10+), license (MIT). Standard open-source practice.
- **D-04:** Show real terminal output for key commands (search, save, warm-up) per DOC-01 requirement.

### Installation Section
- **D-05:** Primary install path: `git clone` + `pip install -r requirements.txt`. This is the established flow (Phase 2 D-01/D-02).
- **D-06:** Mention `uv` as a faster alternative one-liner (`uv pip install -r requirements.txt`), but pip is the primary documented path. Don't force uv on users.
- **D-07:** Installation section must be copy-paste complete: clone, install deps, init vault, warm-up model, configure hooks — no steps requiring external knowledge (DOC-01).

### Example Content
- **D-08:** `examples/` directory contains a single `hooks.json` (or `claude-code-hooks.json`) — the ready-to-use hooks configuration for Claude Code. This is what DOC-04 requires.
- **D-09:** No additional example files beyond the hooks config. Keep examples/ minimal and focused.

### CONTRIBUTING.md
- **D-10:** Standard depth: dev setup instructions, code style (ruff + mypy commands), PR process, issue guidelines. Matches DOC-02 requirements.
- **D-11:** No architecture guide or deep technical docs — this is a single-maintainer project at v1.0.0. Architecture docs can come later if contributors arrive.

### CHANGELOG.md
- **D-12:** Initial entry for v1.0.0 describing the feature set at launch. Keep Changelog format (keepachangelog.com).

### Claude's Discretion
- Exact wording of README value proposition (as long as it's concrete and shows terminal output)
- Badge placement and formatting choices
- CHANGELOG entry categorization (Added/Changed/Fixed sections)
- Whether to include a "How it works" architecture section in README (short diagram is fine if it helps understanding)
- Cost transparency section placement and detail level

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing README
- `README.md` — Current ~15K README with features, quick start, hooks JSON, FAQ. Rewrite target, not greenfield.

### Requirements
- `.planning/REQUIREMENTS.md` — DOC-01 through DOC-04 are the binding requirements
- `.planning/ROADMAP.md` — Phase 3 success criteria define what "done" means

### Prior Phase Decisions
- `.planning/phases/02-code-hardening/02-CONTEXT.md` — D-01 (pyproject.toml metadata-only), D-02 (requirements.txt with == pins) establish install flow

### Project Constraints
- `CLAUDE.md` — Technology stack section for tooling references

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `README.md` (15.4K) — Existing comprehensive README with features list, quick start, hooks JSON config, FAQ. Needs restructuring and rewrite, not starting from scratch.
- `SKILL.md` (18.2K) — Internal skill documentation with usage patterns, may inform README examples
- `pyproject.toml` — Has project metadata (name, description, version) that README should reference

### Established Patterns
- Install flow: `git clone` + `pip install -r requirements.txt` (no package install)
- Default vault path: `~/memo-vault` (replaced from `~/engineering-brain` in Phase 1)
- Hooks config JSON structure already exists in current README — extract to `examples/`
- Scripts in `scripts/` directory — README references these for commands

### Integration Points
- `examples/` directory needs to be created (doesn't exist yet)
- `CONTRIBUTING.md` is a new file
- `CHANGELOG.md` is a new file
- README.md is an existing file to be rewritten

</code_context>

<specifics>
## Specific Ideas

- Current README already has a good hooks JSON config block — extract it to `examples/` for DOC-04 rather than writing from scratch
- DOC-01 explicitly calls for "cost transparency" — the ~$0.002/session Haiku cost should be prominently documented
- README success criteria says "developer can decide yes/no within 60 seconds" — the opening section must be scannable, not wall-of-text
- The 1.1GB model download is a significant gotcha for new users — make it prominent in install steps

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-documentation*
*Context gathered: 2026-04-13*
