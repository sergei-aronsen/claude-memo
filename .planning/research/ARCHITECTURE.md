# Architecture Patterns

**Domain:** Python CLI skill tool for Claude Code (open-source publication)
**Researched:** 2026-04-13
**Confidence:** HIGH (verified against Anthropic's own skills repo and established Python conventions)

---

## Current Architecture (What Exists)

The tool is already built and working in production. Architecture research here focuses on
**how to present and structure it for public open-source release**, not how to design it.

### Existing Component Map

```
claude-memo/
├── SKILL.md                   # Claude Code skill definition (YAML frontmatter + instructions)
├── README.md                  # User-facing documentation
├── LICENSE                    # MIT
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── scripts/                   # Executable scripts (the actual implementation)
│   ├── memo_engine.py         # Core: index, search, dedup, stats (37KB — main module)
│   ├── memo_utils.py          # Shared utilities (14KB)
│   ├── auto_memo.py           # SessionEnd auto-capture via Haiku (9.3KB)
│   ├── session_context.py     # SessionStart context loading (4.2KB)
│   ├── should_suggest_memo.py # Stop hook keyword heuristic (3.8KB)
│   ├── pre_compact_save.py    # PreCompact hook (2.9KB)
│   ├── save_raw_log.py        # Raw log saver (4.3KB)
│   ├── compile_logs.py        # Daily log compilation via cron (5.5KB)
│   ├── memo_mcp_server.py     # MCP server for Claude Desktop/Cursor (9.4KB)
│   ├── auto_memo_hook.sh      # nohup wrapper for SessionEnd (1.6KB)
│   ├── init_vault.sh          # First-run vault setup (6.3KB)
│   └── setup_automation.sh   # Cron + git push + warm-up installer (4.1KB)
│
└── references/                # Internal documentation
    ├── ARCHITECTURE.md        # Existing architecture reference
    └── AUTO_MEMO_SETUP.md     # Automation setup notes
```

### Component Boundaries and Data Flow

```
Claude Code lifecycle events
    │
    ├── SessionStart ──→ session_context.py
    │                       └── reads vault → injects project notes into Claude context
    │
    ├── Stop hook ──→ should_suggest_memo.py
    │                   └── keyword heuristic → nudges user toward /memo (no API cost)
    │
    ├── PreCompact ──→ pre_compact_save.py
    │                   └── saves context before Claude compresses conversation
    │
    └── SessionEnd ──→ auto_memo_hook.sh
                         └── nohup auto_memo.py (detached, survives Claude exit)
                                └── Haiku API → classifies transcript → saves to vault

/memo commands (manual, via SKILL.md)
    └── memo_engine.py        ← central hub for all user-facing operations
          ├── save_raw_log.py   (write path)
          ├── memo_utils.py     (shared utilities)
          └── vault r/w + SQLite + embeddings

memo_mcp_server.py            ← alternative interface for Claude Desktop / Cursor
    └── wraps memo_engine.py

Obsidian vault (source of truth)
    ├── markdown notes (decisions/, patterns/, debug-logs/, insights/, etc.)
    └── .memo/ (derived, gitignored)
          ├── index.db          SQLite + FTS5
          ├── embeddings.npy    numpy vectors (1024 dims)
          ├── id_map.json       note ID ↔ embedding index
          └── write.lock        fcntl exclusive lock

Automation (cron)
    ├── */30 * * * *  → memo_engine.py reindex
    ├── 0 * * * *    → git commit + push
    └── shell login  → memo_engine.py warm-up (background)
```

**Data flow direction:**
1. Claude Code hooks fire → scripts → vault writes
2. /memo commands → memo_engine.py → vault reads/writes
3. Vault is always the source of truth; .memo/ is derived and rebuildable

**Build order implications:**
- memo_utils.py must be stable before touching anything else (shared by 4+ scripts)
- memo_engine.py is the critical path — changes here affect /memo, hooks, and MCP
- Hooks and MCP server are thin wrappers; they can change independently

---

## Recommended Repo Layout for Open-Source Publication

The current layout (`scripts/` + `references/` flat under root) is functional but needs
one addition to match community expectations for contributor experience.

### Recommended Final Layout

```
claude-memo/                     (GitHub repo root)
├── SKILL.md                     # Skill definition — stays at root (Claude Code convention)
├── README.md                    # Primary entry point for newcomers
├── LICENSE                      # MIT — already exists
├── requirements.txt             # Already exists
├── CONTRIBUTING.md              # NEW: how to contribute (see below)
├── CHANGELOG.md                 # NEW: version history
├── .gitignore                   # Already exists
│
├── scripts/                     # Keep as-is — matches existing install path
│   └── [all 12 existing files]
│
├── references/                  # Keep as-is — internal docs
│   ├── ARCHITECTURE.md
│   └── AUTO_MEMO_SETUP.md
│
└── examples/                    # NEW: annotated hook config and settings.json snippets
    ├── hooks-config.json        # Example Claude Code hooks settings block
    └── vault-structure.md       # Diagram of what an initialized vault looks like
```

**What stays vs. what changes:**
- `scripts/` path must NOT change — install instructions in README use `~/.claude/skills/memo-skill/scripts/`
- `SKILL.md` at root is required by Claude Code convention (verified: anthropics/skills repo structure)
- `references/` stays — already referenced in existing docs
- Add `CONTRIBUTING.md`, `CHANGELOG.md`, `examples/` — these are the missing pieces for open-source credibility

### Why This Layout, Not src/ or Flat

**Not src/ layout:** src/ is for installable Python packages distributed via PyPI. This tool
is installed by cloning into a specific path (`~/.claude/skills/memo-skill/`). Making it a
proper package would add complexity (setup.py, pyproject.toml) with no benefit to users.
The scripts are run directly: `python3 scripts/memo_engine.py`.

**Not fully flat:** Flat layout would mix Python scripts with markdown docs and shell scripts.
The existing `scripts/` separation is cleaner and matches how Claude Code skills are typically
structured (see alirezarezvani/claude-skills, anthropics/skills examples).

**Current structure is already correct** for the use case — a Claude Code skill distributed
via git clone. The only gap is missing contributor-experience files.

---

## Patterns to Follow

### Pattern 1: SKILL.md at Root with Full Frontmatter
**What:** SKILL.md must live at the repo root with name, description, and trigger phrases in YAML frontmatter.
**When:** Always — this is how Claude Code discovers and loads skills.
**Why:** Anthropic's own skills repo confirms: "Each skill is a self-contained folder with SKILL.md as the only required file."

### Pattern 2: Installation Path Convention
**What:** Skills are installed to `~/.claude/skills/<skill-name>/` by convention.
**When:** All README install instructions and all hardcoded paths in scripts must use this convention.
**Why:** Claude Code's settings.json skill discovery looks in `~/.claude/skills/` by default.

### Pattern 3: Hooks as Thin Wrappers
**What:** Claude Code hooks should be minimal — just enough to call the real script.
**When:** SessionEnd hook specifically must be thin because Claude Code exits right after firing it.
**Why:** `auto_memo_hook.sh` correctly uses `nohup + disown` — the pattern to document as canonical.

### Pattern 4: Derived Artifacts Are Gitignored
**What:** The `.memo/` directory (index.db, embeddings.npy, id_map.json) is gitignored.
**When:** Always — these are rebuilt from the vault and can be 100MB+ after heavy use.
**Why:** Vault is source of truth; index is a cache. Including it would bloat the user's repo.

### Pattern 5: examples/ for Copy-Paste Config
**What:** An `examples/` directory with a complete `settings.json` hooks block that users can paste directly.
**When:** Any tool with a non-trivial JSON config that users must write by hand.
**Why:** The current README has hooks JSON inline in the markdown — hard to keep in sync, hard to copy. A standalone file is better.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Packaging as a pip-installable CLI
**What:** Adding `pyproject.toml`, entry_points, `setup.py` to make `pip install claude-memo` work.
**Why bad:** The skill must live at a specific path (`~/.claude/skills/memo-skill/`) for Claude Code
to find it. `pip install` would put it in site-packages, breaking the hook paths. The install
story is already simple: `git clone` + `pip install sentence-transformers`.
**Instead:** Keep git-clone installation. Document it clearly.

### Anti-Pattern 2: Versioning the .memo/ Index in Git
**What:** Accidentally committing `.memo/embeddings.npy` or `index.db`.
**Why bad:** Embeddings grow with vault size. A 500-note vault generates ~4MB embeddings.npy.
Anyone who forks or clones the repo gets stale index data.
**Instead:** Confirm `.gitignore` includes `.memo/` before publish (already in place).

### Anti-Pattern 3: CONTRIBUTING.md That Lists Everything
**What:** Long contribution guides covering code style, test suites, CI, release process.
**Why bad:** This is a single-maintainer tool at v1. An 8-page CONTRIBUTING.md signals bureaucracy,
not welcome.
**Instead:** Short, honest CONTRIBUTING.md: "here's how to run it locally, here's what good issues
look like, PRs welcome for X." 100-150 lines max.

### Anti-Pattern 4: Separate branches per environment
**What:** `main` for stable, `dev` for development, `experimental` for new features.
**Why bad:** Overkill for a single-maintainer open-source skill tool. Confuses contributors
about where to target PRs.
**Instead:** Single `main` branch. Use tags for releases (v1.0.0, v1.1.0).

---

## Contributor Experience — Minimum Viable Set

Based on research into Python open-source conventions and the Claude Code ecosystem:

| File | Required | Content |
|------|----------|---------|
| README.md | YES (exists) | Problem, install, quick start, hook config, /memo commands |
| LICENSE | YES (exists) | MIT |
| requirements.txt | YES (exists) | With comments (already has them) |
| SKILL.md | YES (exists) | Claude Code skill definition |
| CONTRIBUTING.md | YES (missing) | Local setup, issue guidelines, PR welcome scope |
| CHANGELOG.md | YES (missing) | v1.0.0 initial release entry at minimum |
| examples/ | RECOMMENDED (missing) | Copy-paste hooks config JSON |
| tests/ | NOT required at v1 | Scripts have no test suite; honest gap |
| docs/ | NOT required | references/ is sufficient for now |
| CODE_OF_CONDUCT.md | NOT required | Optional for small tools; adds friction |

**Build order for open-source publication:**
1. Sensitive data scan (before anything else)
2. CONTRIBUTING.md (one-time, low effort)
3. CHANGELOG.md (v1.0.0 entry)
4. examples/ directory (2 files: hooks-config.json, vault-structure.md)
5. README polish (ensure install path matches `claude-memo` repo name)
6. GitHub repo creation + push

---

## Scalability Considerations

This is a local tool — "scalability" means vault size, not concurrent users.

| Concern | At 50 notes | At 500 notes | At 5000 notes |
|---------|-------------|--------------|---------------|
| Reindex time | ~10s | ~90s | ~15min |
| Search latency | <100ms | <100ms | <200ms |
| Model RAM | ~1.5GB (fixed) | ~1.5GB (fixed) | ~1.5GB (fixed) |
| embeddings.npy size | ~200KB | ~2MB | ~20MB |

The architecture handles scale correctly: RAM is constant (model size, not vault size),
search stays fast at any scale, only reindex is slow (and runs as background cron).

---

## Sources

- [Anthropic official skills repo structure](https://github.com/anthropics/skills) — HIGH confidence
- [Python Hitchhiker's Guide — project structure](https://docs.python-guide.org/writing/structure/) — HIGH confidence
- [Python Packaging: src vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — HIGH confidence
- [claude-code-hooks-mastery repo pattern](https://github.com/disler/claude-code-hooks-mastery) — MEDIUM confidence
- [awesome-claude-code skill patterns](https://github.com/hesreallyhim/awesome-claude-code) — MEDIUM confidence
- [pyopensci CONTRIBUTING.md guide](https://www.pyopensci.org/python-package-guide/documentation/repository-files/contributing-file.html) — HIGH confidence
- Existing `references/ARCHITECTURE.md` in memo-skill — HIGH confidence (source of truth for component map)
