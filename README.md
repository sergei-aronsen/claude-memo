# Memo

Persistent engineering memory for Claude Code. Automatic capture, semantic search, cross-project intelligence.

![CI](https://github.com/sergei-aronsen/claude-memo/actions/workflows/ci.yml/badge.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

Claude Code forgets everything between sessions. Memo builds a persistent knowledge vault — every architecture decision, debug solution, and code pattern is captured automatically and searchable by meaning. One vault across all projects.

## Before / After

```
# Without Memo — session 14, same bug again
$ claude
> How do I configure CORS for a FastAPI backend with a React frontend?
  [20 minutes of debugging headers, middleware order, allowed origins...]

# With Memo — Claude loads the fix at session start
$ claude
  [SessionStart hook: loading 3 relevant notes from vault]
> How do I configure CORS for a FastAPI backend with a React frontend?
  I found your previous solution in the vault:
    decisions/2026-03-15-fastapi-cors-config.md (similarity: 0.91)

  You solved this using fastapi.middleware.cors.CORSMiddleware with
  allow_origins=["http://localhost:3000"], allow_credentials=True.
  The key was middleware order — CORS must be added before other middleware.
```

## Features

**Semantic search** — Find notes by meaning, not just keywords. Search "авторизация" and find your note titled "JWT refresh token strategy". Powered by `multilingual-e5-large` (1024 dims, 50+ languages).

**Automatic capture** — SessionEnd hook classifies every conversation via Claude Haiku (~$0.002/session). Decisions, patterns, debug solutions saved automatically.

**Smart context loading** — SessionStart hook detects your project and loads relevant notes into Claude's context. Every session starts informed.

**Mid-session nudges** — Stop hook detects decision-making language and suggests `/memo`. Zero API cost — pure keyword heuristic.

**Obsidian-native** — Vault is plain markdown with YAML frontmatter and `[[wikilinks]]`. Open in Obsidian for graph view. Git-versioned from day one.

**Deduplication** — Semantic similarity check before every save. Related notes are linked rather than fragmented.

**Cross-project intelligence** — One vault for all projects. Tags and wikilinks connect patterns across codebases.

**Race-safe** — File locking via `fcntl.flock` on all write operations. Multiple concurrent sessions won't corrupt the index.

## Requirements

- Python 3.10+
- Claude Code (for hooks integration)
- ~1.5GB RAM for the embedding model

> **Note:** Installation downloads `intfloat/multilingual-e5-large` (~1.1GB, one-time). This happens in Step 4 below. Plan accordingly on metered connections.

- `ANTHROPIC_API_KEY` — optional, required only for auto-memo classification via Haiku (~$0.002/session). Manual `/memo` works without it.
- Obsidian — optional, for graph visualization.

## Installation

### 1. Clone

```bash
git clone https://github.com/sergei-aronsen/claude-memo.git ~/.claude/skills/memo-skill
```

### 2. Install dependencies

```bash
cd ~/.claude/skills/memo-skill
pip install -r requirements.txt
# Alternative (faster): uv pip install -r requirements.txt
```

### 3. Initialize vault

```bash
bash ~/.claude/skills/memo-skill/scripts/init_vault.sh ~/memo-vault
```

This creates the vault directory structure and initializes git.

### 4. Download embedding model (~1.1GB, one-time, takes 2-5 minutes)

```bash
python3 ~/.claude/skills/memo-skill/scripts/memo_engine.py warm-up
```

Model: `intfloat/multilingual-e5-large`. Downloads once, cached at `~/.cache/memo-models`. Runs locally — no API calls, no cost.

### 5. Set up automation

```bash
bash ~/.claude/skills/memo-skill/scripts/setup_automation.sh ~/memo-vault
```

Installs: cron reindex every 30 min, git auto-push every hour, model warm-up at terminal login.

### Environment variables

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export MEMO_VAULT_PATH=~/memo-vault
export ANTHROPIC_API_KEY=your-key-here  # Required for auto-memo; omit to use manual /memo only
```

Reload: `source ~/.zshrc` (or restart terminal).

### Configure hooks

Copy `examples/hooks.json` into your `~/.claude/settings.json`, or add the hooks manually:

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

What each hook does:

- **SessionStart** — loads project note + recent decisions into context at session start
- **SessionEnd** — saves raw daily log (fast, no API) + classifies transcript via Haiku (background)
- **PreCompact** — saves context before Claude compresses it mid-session
- **Stop** — nudges Claude to suggest `/memo` when decision-making language detected

Done. Start working. Your vault fills itself.

## Usage

### Save knowledge

```
/memo
```

Claude infers the note type (decision, pattern, debug fix, insight, tool) and creates a structured Zettelkasten note with frontmatter and wikilinks.

Example output:

```
Saved: decisions/2026-04-13-postgresql-jsonb-vs-separate-tables.md
Type: decision | Tags: database, architecture
Links created: [[projects/my-api]], [[decisions/2026-03-20-orm-choice]]
```

### Search your vault

```
/memo find how did I solve the CORS issue
/memo find авторизация JWT
```

Combined semantic + keyword search. Finds related notes even with different wording.

Example output:

```
Found 3 results for "CORS issue":

1. debug-logs/2026-03-15-fastapi-cors-config.md (score: 0.91)
   FastAPI CORS middleware — CORSMiddleware must be added before other middleware...

2. patterns/2026-02-10-cors-headers-pattern.md (score: 0.74)
   CORS headers pattern — allow_credentials requires explicit origin, not wildcard...

3. decisions/2026-01-22-api-gateway-cors.md (score: 0.61)
   API gateway CORS handling — delegated to nginx upstream config...
```

### Query from terminal (no Claude Code needed)

```bash
python3 ~/.claude/skills/memo-skill/scripts/memo_engine.py query "how did I solve the CORS issue" --vault ~/memo-vault
```

Finds relevant notes via semantic + keyword search, sends them to Haiku, returns a synthesized answer with sources. Cost: ~$0.001/query.

### All commands

| Command | What it does |
|---------|-------------|
| `/memo` | Save a new note (decision, pattern, debug, insight, tool) |
| `/memo find {query}` | Semantic + keyword search across all notes |
| `/memo query {question}` | Search + LLM-synthesized answer (also works from terminal) |
| `/memo list` | Show last 10 notes with type and summary |
| `/memo project` | Create/update project overview note |
| `/memo dedup` | Find and resolve duplicate notes |
| `/memo lint` | 7 health checks: broken links, orphans, empty notes |
| `/memo stats` | Vault statistics: notes by type, tags, connections |
| `/memo link` | Connect two notes with wikilinks |
| `/memo reindex` | Rebuild search index from vault files |

## How it works

```
┌──────────────────────────────────────────────────────┐
│ Claude Code                                          │
│                                                      │
│ SessionStart → load project context from vault       │
│ Stop hook → keyword nudge → suggest /memo            │
│ /memo commands → memo_engine.py → vault + index      │
│ SessionEnd → auto_memo.py → classify → auto-save     │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│ Obsidian Vault (source of truth)                     │
│                                                      │
│ decisions/ patterns/ debug-logs/ insights/            │
│ tools/ references/ projects/ INDEX.md                 │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│ .memo/ (derived index, gitignored)                   │
│                                                      │
│ index.db ← SQLite + FTS5 (keyword search)            │
│ embeddings.npy ← 1024-dim vectors (semantic search)  │
│ write.lock ← fcntl file lock (concurrency safety)    │
└──────────────────────────────────────────────────────┘
```

Three layers:

1. **Obsidian vault** — human-readable markdown, git-versioned, portable
2. **SQLite + FTS5** — instant keyword search on titles, tags, aliases, content
3. **Embeddings** — semantic search via `intfloat/multilingual-e5-large` (local, free)

The vault is the source of truth. The index is derived — always rebuildable via `/memo reindex`.

## Auto-capture layers

Five layers ensure nothing falls through the cracks:

| Layer | When | How | Cost |
|-------|------|-----|------|
| **Stop hook** | Every Claude response | Keyword heuristic → nudges Claude to suggest `/memo` | $0 |
| **PreCompact hook** | Mid-session compression | Saves last 30 messages before Claude discards details | $0 |
| **SessionEnd Stage 1** | Session closes | Raw daily log saved instantly (no API) | $0 |
| **SessionEnd Stage 2** | After exit (background) | Transcript → Haiku → structured memos | ~$0.002 |
| **Compile (cron)** | Daily at 18:00 | Batch-processes all daily logs → wiki articles | ~$0.01/day |

Two-stage pipeline at SessionEnd: Stage 1 saves a raw daily log immediately (survives even if Stage 2 fails). Stage 2 runs detached via `nohup + disown`, calls Haiku to classify, creates structured memos. The `compile_logs.py` cron job catches anything both stages missed.

## Cost

| Operation | Cost | Notes |
|-----------|------|-------|
| Embedding model | Free | Runs locally, one-time 1.1GB download |
| Auto-memo classification | ~$0.002/session | Claude Haiku; session summary only, not full code |
| Terminal query | ~$0.001/query | Haiku synthesizes answer from relevant notes |
| Manual `/memo` only | Free | No API calls if `ANTHROPIC_API_KEY` is not set |

**At 5 sessions/day: ~$1/month.** You can also use Memo with zero API cost — just skip `ANTHROPIC_API_KEY` and use `/memo` manually.

## Note format

Every note is an atomic Zettelkasten card:

```markdown
---
type: decision
created: 2026-04-11
updated: 2026-04-11
project: my-saas-project
tags:
  - database
  - architecture
aliases:
  - PostgreSQL vs MongoDB
  - DB choice for metadata
---

# PostgreSQL jsonb vs separate tables for job metadata

## Context

Choosing data model for my-saas-project. Need flexible schema
for varying formats across multiple API sources.

## Decision

PostgreSQL with jsonb columns. Keeps relational integrity for core
fields (id, company, date) while allowing flexible metadata per source.

## Alternatives Considered

MongoDB — better for pure document storage, but relational joins
are needed for the analytics dashboard. Two databases = operational overhead.

## Consequences

Schema migrations are simpler (jsonb is schema-on-read).
Trade-off: jsonb queries are slower than indexed columns for
complex filters. Acceptable at current scale.

## Related

- [[decisions/2026-03-15-api-architecture]]
- [[projects/my-saas-project]]
```

## Vault structure

```
memo-vault/
├── INDEX.md                    ← chronological log of all notes
├── decisions/                  ← architecture choices, tech stack picks
├── patterns/                   ← reusable code patterns and approaches
├── debug-logs/                 ← bug fixes, error solutions, workarounds
├── insights/                   ← learnings, observations, discoveries
├── tools/                      ← tool configs, CLI commands, setup procedures
├── references/                 ← external knowledge, article summaries
├── projects/                   ← project overviews (navigational hubs)
├── daily-logs/                 ← raw session logs (auto-captured)
│   ├── 2026-04-11.md           ← compiled → wiki articles
│   └── 2026-04-12.md           ← pending compilation
├── .memo/                      ← search index (gitignored, rebuildable)
│   ├── index.db                ← SQLite + FTS5
│   ├── embeddings.npy          ← numpy vectors (1024 dims)
│   └── auto_memo.log           ← auto-capture log
├── .obsidian/                  ← Obsidian config (color-coded graph)
└── .gitignore                  ← excludes .memo/
```

## Configuration

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEMO_VAULT_PATH` | `~/memo-vault` | Vault location |
| `MEMO_MODEL_CACHE` | `~/.cache/memo-models` | Embedding model cache |
| `ANTHROPIC_API_KEY` | — | Required for auto-memo (Haiku) and terminal queries |

### Automation (installed by `setup_automation.sh`)

- Cron reindex every 30 min — catches Obsidian edits
- Cron git push every hour — backup to remote
- Model warm-up at terminal login — eliminates cold start delay

## FAQ

**Does it send my code to the cloud?**
No. Embeddings run 100% locally via `multilingual-e5-large`. The only outbound call is auto-memo classification via Claude Haiku — this sends a session summary, not your code. You can disable auto-memo entirely by not setting `ANTHROPIC_API_KEY`.

**What about the 1.1GB download?**
The embedding model downloads once to `~/.cache/memo-models` and is cached permanently. After that, warm-up at terminal login takes ~3 seconds. No repeated downloads. If you're on a metered connection, run Step 4 on Wi-Fi.

**What if I close the terminal accidentally?**
SessionEnd fires on Ctrl+C, Ctrl+D, window close, and `/exit`. The auto-memo hook detaches from the process and runs independently. Only a hard crash or power loss prevents capture — and even then, the transcript file remains on disk for manual recovery.

**How much does it cost?**
Embedding model is free (local). Auto-memo uses ~$0.002 of Haiku per session. At 5 sessions/day: ~$1/month. Manual `/memo` with no `ANTHROPIC_API_KEY` set is completely free.

**Can I use it without Obsidian?**
Yes. The vault is plain markdown — works with any text editor, VS Code, or just `grep`. Obsidian adds graph visualization and wikilink navigation but isn't required.

**Does it work with non-Claude Code editors?**
The `/memo` commands are Claude Code specific. But the vault and search engine work standalone — `python3 memo_engine.py search "query" --vault ~/memo-vault` runs from any terminal.

**What about multilingual content?**
`multilingual-e5-large` supports 50+ languages. Search "авторизация" and find notes titled "JWT authentication". Tags are always in English for consistency; note content can be in any language.

**Can I access my vault from other projects?**
Yes — add this to `CLAUDE.md` in any project:

```markdown
## Knowledge Base
When answering architecture or implementation questions, first check the
engineering knowledge vault at ~/memo-vault
Read INDEX.md first, then navigate to relevant wiki articles.
Use /memo to save new decisions and patterns.
```

One snippet, no hooks needed. Works alongside the SessionStart hook.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition — triggers, commands, quality guidelines |
| `scripts/memo_engine.py` | Core engine: SQLite + FTS5 + embeddings + lint + query |
| `scripts/auto_memo.py` | Auto-classify transcripts via Haiku |
| `scripts/auto_memo_hook.sh` | SessionEnd wrapper: Stage 1 (raw log) + Stage 2 (classify, detached) |
| `scripts/save_raw_log.py` | Stage 1: fast daily log dump, no API |
| `scripts/compile_logs.py` | Cron: batch-compile daily logs → structured wiki articles |
| `scripts/pre_compact_save.py` | PreCompact hook: saves context before mid-session compression |
| `scripts/session_context.py` | SessionStart: load project context from vault |
| `scripts/should_suggest_memo.py` | Stop hook: keyword nudge for `/memo` |
| `scripts/init_vault.sh` | Vault + Obsidian + git initialization |
| `scripts/setup_automation.sh` | Cron + warm-up + env var setup |
| `examples/hooks.json` | Ready-to-use hooks config for `~/.claude/settings.json` |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.

## License

MIT — see [LICENSE](LICENSE)
