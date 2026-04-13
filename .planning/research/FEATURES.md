# Feature Landscape: claude-memo

**Domain:** AI-assisted engineering memory / knowledge vault for Claude Code
**Researched:** 2026-04-13
**Milestone context:** Open-source publication + README polish

---

## Table Stakes

Features users expect when they find this project. Missing = leave for a competing tool.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Clear installation instructions | Every well-maintained tool has them. Devs abandon if setup takes >5 min. | Low | Step-by-step, tested on clean machine. Already exists in some form — needs polish. |
| README with "what problem this solves" | First 10 seconds: user decides to stay or leave. | Low | Value prop must land in 2 sentences. |
| MIT or permissive license | Devs won't adopt tools with viral licenses (GPL) for personal tooling. MIT already in place. | Low | Already done. |
| Persistent memory across sessions | This is the core product. Without it, no reason to exist. | High | Fully implemented. |
| Semantic search over past decisions | Users need retrieval by meaning, not just keyword. Ecosystem standard. | High | Implemented (multilingual-e5-large). |
| Auto-capture without manual effort | Users won't remember to save. Competition (claude-mem, mcp-memory-service) all auto-capture. | High | Implemented via hooks. |
| Local-first storage (no cloud dependency) | Privacy-sensitive developer logs. Users explicitly seek local solutions. | Medium | Implemented (SQLite + markdown vault). |
| MCP server support | Standard integration path for Claude Desktop and Cursor. All competing tools expose MCP. | Medium | Implemented. |
| Python 3.10+ compatibility | Standard modern Python target. Lower version blocks adoption. | Low | Already met. |
| No API keys required for core function | Tools requiring OpenAI keys for embedding lose privacy-first users immediately. | Medium | Implemented (local ONNX/sentence-transformers). |
| CONTRIBUTING.md | Without it, PRs and issues have no process. Discourages contributors. | Low | Needs creation. |
| Sensitive data absence | Pre-publication security scan. Users fork and extend — no personal data in git history. | Low | Explicit requirement in PROJECT.md — needs verification pass. |
| Basic usage examples in README | "One command to start seeing value." Without examples, docs feel incomplete. | Low | Needs examples section. |

---

## Differentiators

Features that set claude-memo apart from competitors. Not universally expected, but valued by the target user.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Obsidian-native vault output | Unlike all competitors (SQLite-only, chroma-only), every memory is a plain .md file readable without the tool. Zero lock-in. | Medium | Unique in ecosystem. claude-mem uses SQLite+Chroma. mcp-memory-service uses SQLite. Neither produces Obsidian-compatible output. |
| Cross-project intelligence via single vault | Most tools scope memory per-project. claude-memo scans across projects with wikilinks and tags. | Medium | Implemented. Competitors like mcp-memory-keeper are project-scoped by design. |
| Mid-session nudges via Stop hook | Captures important moments before they're lost to compression. No competing tool does this. | Low | Implemented. Unique hook combination. |
| PreCompact hook context preservation | Saves context just before Claude compacts — prevents data loss at the worst moment. | Low | Implemented. Not seen in other tools. |
| Semantic deduplication before save | Prevents vault bloat. Competing tools allow duplicate entries. | Medium | Implemented. |
| Vault health tooling (/memo lint) | Operational tooling beyond just capture. Shows maturity. | Low | Implemented. |
| Multilingual embedding model | 50+ language support via multilingual-e5-large. Competitors use English-only embeddings. | Medium | Differentiator for non-English developers. |
| Daily log compilation via cron | Temporal log of what was worked on — like a developer journal. Not available in competitors. | Low | Implemented. |
| $0.002/session cost transparency | Honest cost disclosure (Haiku for classification). Users trust tools that are upfront about costs. | Low | Should be prominently stated in README. |
| Race-safe concurrent writes (fcntl.flock) | Multi-session safety. Competing Python tools don't handle this explicitly. | Low | Implemented. Worth calling out in docs. |

---

## Anti-Features

Features to deliberately NOT build for this milestone (open-source publication).

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web UI / dashboard | claude-code-organizer builds this (250 stars). Scope creep for a publish milestone. Users already have Obsidian. | Reference Obsidian as the UI layer in README. |
| Cloud sync infrastructure | Out of scope per PROJECT.md. Adds operational complexity and breaks local-first story. | Document git push via cron as the sync story. |
| Support for non-Claude assistants (Copilot, Cursor native) | Dilutes focus. MCP already covers Claude Desktop + Cursor. Maintain hook specificity. | State Claude Code as primary target clearly in README. |
| Interactive setup wizard / installer script | Over-engineering for publish milestone. pip install + manual hook config is the standard in this ecosystem. | Clear step-by-step in README is sufficient. |
| Multi-user / team shared vault | Completely different architecture. No demand signal yet. | Mark as "Out of Scope" in README explicitly. |
| Plugin/extension marketplace | Zero community yet. Build community first. | Add to future ideas after gauging adoption. |
| Auto-summarization using paid LLM APIs | Creates dependency and cost unpredictability. Haiku is already the cap for classification only. | Keep Haiku for classification only, local embeddings for search. |
| Memory editing / correction UI | Vault is plain markdown — users edit directly in Obsidian. Building a parallel editor is redundant. | Point to Obsidian for editing. |
| Token usage dashboard | Covered by existing tools (claude-code-organizer). Not the core value of this project. | Defer or explicitly out of scope. |

---

## Feature Dependencies

```
Auto-capture (SessionEnd hook)
  → Haiku classification (requires ANTHROPIC_API_KEY)
  → Semantic dedup → Save to Obsidian vault
      → SQLite FTS5 index
      → Markdown + YAML frontmatter
          → Obsidian wikilinks (cross-project intelligence)

SessionStart hook
  → Smart context loading (requires SQLite FTS5 + semantic search)
      → multilingual-e5-large embeddings (requires sentence-transformers)

PreCompact hook → Save context snapshot → vault

Stop hook (mid-session nudge) → keyword heuristic (no cost) → prompt user

MCP server → exposes search to Claude Desktop/Cursor
  → requires memo_engine.py running

/memo lint → requires vault path configured → checks markdown structure

Daily log via cron → requires vault path + existing entries
```

Key dependency: **ANTHROPIC_API_KEY** is required for classification (Haiku). This must be called out in README — without it, auto-capture saves but without topic classification. Not a blocker but affects output quality.

---

## Open-Source Publication Feature Requirements

This section specifically addresses the "publish milestone" context.

### Must-Have for Publication

| Item | Why | Status |
|------|-----|--------|
| README: 1-sentence value prop | First 10 seconds retention | Needs writing |
| README: installation steps (tested clean) | Devs abandon broken installs | Needs writing/testing |
| README: usage examples with real output | Shows what you actually get | Needs writing |
| README: cost disclosure ($0.002/session) | Trust builder | Needs writing |
| README: what it does NOT do | Sets expectations, prevents bad issues | Needs writing |
| CONTRIBUTING.md | Enables community PRs | Needs creation |
| Sensitive data scan (code + git history) | Pre-publication requirement | Needs audit |
| .gitignore covering vault path | Don't accidentally commit personal vault | Needs verification |
| GitHub topics/tags | Discoverability: `claude-code`, `memory`, `obsidian`, `mcp` | Needs setup |
| License visible in README badge | Trust signal at a glance | Needs badge |

### Nice-to-Have for Publication

| Item | Why | Status |
|------|-----|--------|
| CHANGELOG.md | Shows project is maintained | Low effort, high trust signal |
| GitHub Actions: basic lint CI | Shows active maintenance | Low effort |
| GitHub issue templates | Reduces low-quality bug reports | Low effort |
| Comparison section in README vs competing tools | Helps users choose confidently | Medium effort |
| Architecture diagram (ASCII or mermaid) | Developers want to understand internals before adopting | Medium effort |
| Python package on PyPI | One-command install vs git clone | Medium effort — not required for publish milestone |

### Explicitly Defer

| Item | Why Defer |
|------|-----------|
| PyPI packaging | Adds maintenance burden. git clone works for first release. |
| Homebrew formula | Premature. Build adoption first. |
| Docker image | Over-engineering for a Python CLI tool with local vault. |
| GitHub Discussions | Enable only after seeing issue volume. |

---

## Competitive Feature Matrix

| Feature | claude-memo | claude-mem | mcp-memory-service | WhenMoon memory-mcp |
|---------|-------------|------------|-------------------|---------------------|
| Auto-capture via hooks | Yes (5 hooks) | Yes (5 hooks) | No (manual) | No (manual) |
| Semantic search | Yes (local) | Yes (Chroma) | Yes (ONNX local) | No |
| Obsidian-native output | **Yes (unique)** | No | No | No |
| Cross-project memory | **Yes** | No | No | No |
| Local-first | Yes | Yes | Yes | Yes |
| MCP server | Yes | No | Yes | Yes |
| Cost per session | $0.002 (Haiku) | ~$0 (no LLM classify) | $0 | $0 |
| Mid-session nudge | **Yes (Stop hook)** | No | No | No |
| PreCompact hook | **Yes** | No | No | No |
| Deduplication | **Yes** | No | Decay-based | No |
| License | MIT | AGPL-3.0 | Apache 2.0 | Not stated |

Confidence: MEDIUM — competitor features inferred from READMEs, some may have undocumented features.

---

## MVP Recommendation for Open-Source Publication

**Publish as-is functionally** — the feature set is already beyond competitors in several dimensions.

**Focus the milestone entirely on trust signals and discoverability:**

1. Clean, scannable README with value prop, install steps, examples
2. Sensitive data audit (non-negotiable blocker)
3. CONTRIBUTING.md (enables community before launch)
4. GitHub topics for discoverability
5. Cost transparency prominently stated

**Defer:** PyPI packaging, advanced CI, architecture diagrams — these are iteration 2 after gauging adoption.

---

## Sources

- [GitHub: thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) — AGPL-3.0, hooks-based memory, Chroma+SQLite, web UI
- [GitHub: doobidoo/mcp-memory-service](https://github.com/doobidoo/mcp-memory-service) — REST API, knowledge graph, ONNX embeddings
- [GitHub: WhenMoon-afk/claude-memory-mcp](https://github.com/WhenMoon-afk/claude-memory-mcp) — MCP-native, SQLite, graph navigation
- [GitHub topics: claude-memory](https://github.com/topics/claude-memory) — ecosystem overview, star counts
- [Top 10 AI Memory Products 2026](https://medium.com/@bumurzaqov2/top-10-ai-memory-products-2026-09d7900b5ab1) — Mem0, Zep, LangMem, Letta landscape
- [6 Open-Source AI Memory Tools](https://medium.com/@jununhsu/6-open-source-ai-memory-tools-to-give-your-agents-long-term-memory-39992e6a3dc6) — framework survey
- [Open Source Checklist (GSA)](https://github.com/GSA/open-source-policy/blob/master/OpenSource_code/open_source_checklist.md) — publication requirements
- [Make a README](https://www.makeareadme.com/) — README standard structure
