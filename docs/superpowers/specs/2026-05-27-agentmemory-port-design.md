# Design: port best functional features from agentmemory into claude-memo

Date: 2026-05-27
Status: approved (scope: "реализуй все, что считаешь нужным")

## Goal

Close the functional gaps with `agentmemory` that fit a **solo Obsidian-vault**
use case. Explicitly **out of scope**: multi-agent (leases/signals/team) and the
graph search stream — low value for a single-user markdown vault and high
complexity. agentmemory itself ships graph/reranking off by default.

## What already exists (reuse, do not rebuild)

- `search_vault` — RRF fusion of semantic (e5) + keyword (FTS5). `RRF_K=60`.
- `find_contradictions` — cosine-band + polarity heuristic, returns a review list.
- `find_stale_notes` — `recall_count==0 & old` OR `last_recalled` older than N days.
- `derive_tier` + `_TYPE_TO_TIER` — episodic / semantic / procedural.
- recall tracking — `last_recalled`, `recall_count` columns, stamped on search hits.
- `save_memo_and_index` — single atomic save+index entry point under `VaultLock`.
- `build_frontmatter` / `parse_frontmatter` — frontmatter read/write.

## Features

### F1 — Decay / auto-forget (archive-only, never delete)

New `archive_stale_notes(vault_path, days=90, apply=False, limit=200)` in
`memo_engine.py`.

- Candidates from `find_stale_notes`, then **tier-aware** filtering:
  - `episodic` (debug, daily-log): eligible at `days`.
  - `semantic` / `procedural`: eligible only if `recall_count==0` AND age >
    `days * SEMANTIC_AGE_MULT` (default 3×) AND **no inbound wikilinks**
    (no other note links to it — orphan).
- Value proxy (claude-memo has no `importance` field): `recall_count` + tier +
  inbound-wikilink degree.
- `apply=False` (default) → dry-run report only. `apply=True` performs archive.
- Archive action (under `VaultLock`):
  1. move file to `<vault>/archive/<original-relpath>`,
  2. set frontmatter `status: archived`, `archived_at`, `archived_reason`,
  3. drop from FTS + embeddings so default search skips it.
- Reversible: file preserved in `archive/`, git history intact.
- Surfaces: CLI `decay [--apply] [--days N]`, MCP `memo_decay`.

### F2 — Search diversification

`search_vault` gains `max_per_project: int | None = 3`.

- After RRF sort, greedily select respecting the per-project cap until `limit`
  reached, then fill any remaining slots ignoring the cap (never return fewer
  than before). `None` disables (legacy behaviour).
- Needs candidate `project` fetched before the final trim.

### F3 — Versioning / supersedes

- New column `status TEXT` + `superseded_by TEXT` (additive `ALTER TABLE`,
  same pattern as recall columns).
- `detect_supersede(note_id, vault, conn, store, ...)`: reuse contradiction
  logic for the one new note vs existing notes. On a **high-confidence**
  contradiction (cosine ≥ 0.90, opposite polarity, target older) mark the
  **older** note `status: superseded`, `superseded_by: [[new]]`.
- `search_vault` filters `status='superseded'` and `status='archived'` unless
  `include_superseded=True`.
- Conservative + reversible (frontmatter edit). Default on; disable via
  `MEMO_AUTO_SUPERSEDE=0`.

### F4 — Query expansion (opt-in)

- Env-gated `MEMO_QUERY_EXPANSION=1` (off by default — adds LLM latency/cost
  per search).
- Generate 2–3 reformulations via `call_llm` (sandwich prompt: system rules
  separate from user query), search each, merge by note_id keeping max RRF.
- Reuses the existing provider client + SSRF allowlist.

### F5 — Hooks (+ targeted, not noisy)

- Add **SubagentStop** capture only — reuses the existing auto-memo
  classification pipeline (high signal, low frequency).
- Explicitly **reject** raw `PostToolUse` capture: claude-memo writes curated
  markdown notes; per-tool capture would flood the vault. agentmemory's "12
  hooks" work because it captures to cheap KV with dedup + later consolidation.

## Quality bar

- Each feature = atomic commit + tests.
- CI must stay green: `ruff check`, `ruff format`, `mypy scripts/`,
  `bandit -r scripts/ -ll`, `pytest`.
- No hard deletes. All destructive-looking ops are archive/mark + reversible.
- Follow existing security patterns (size caps, SSRF allowlist, `VaultLock`,
  `_path_in_vault` traversal guard).
