# Phase 1: Security & Cleanliness - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Audit and sanitize the clean copy of memo-skill source code (`~/Downloads/memo-skill/`) before any git history is created in the target repo. Copy sanitized files into this repo (`~/Projects/claude-memo/`), verify zero sensitive data, and prepare for a single clean initial commit.

</domain>

<decisions>
## Implementation Decisions

### Source handling
- **D-01:** Copy files from `~/Downloads/memo-skill/` into this repo (`~/Projects/claude-memo/`). Work on the copy, not the original.
- **D-02:** The clean copy in Downloads is the source of truth — never copy from the installed version at `~/.claude/skills/memo-skill/` (confirmed to contain personal project names).

### Vault path naming
- **D-03:** Replace all occurrences of `~/engineering-brain` with `~/memo-vault` (9 occurrences across scripts). This is a neutral, descriptive default.
- **D-04:** Ensure `MEMO_VAULT_PATH` environment variable remains the primary override mechanism.

### README example content
- **D-05:** Replace real project/company names in README examples with generic alternatives:
  - `JobHunter.no` → `my-saas-project` or similar
  - `Finn.no`, `Webcruiter`, `Jobbnorge` → generic data source names
  - Any real-world project references → fictional but realistic examples
- **D-06:** Preserve the structure and educational value of examples — only change identifying names.

### Scan scope
- **D-07:** Use comprehensive scan covering:
  - Patterns from MEMO_GITHUB_PUBLISH.md: `sergeiarutiunian`, `sk-or-v1-`, `sk-ant-api`, `@gmail`, `password`, `Dropbox/WORK`, `jobhunter`, `digital-planet`, `cookie-consent`, `Digital Planet`, `Lillestrøm`
  - Additional common patterns: absolute home paths (`/Users/`), API keys, tokens, email addresses
  - Scan all file types: `.py`, `.sh`, `.md`, `.txt`, `.json`
- **D-08:** After automated scan, do a manual review of README examples section for subtle personal references.

### Git workflow
- **D-09:** Single clean commit after all sanitization is verified. No intermediate history with personal data.

### Claude's Discretion
- Exact wording of generic example replacements (as long as they're realistic and educational)
- Order of scan/replace operations
- Whether to add a pre-commit hook for sensitive data scanning (defer to Phase 2 if yes)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Publication instructions
- `~/Downloads/MEMO_GITHUB_PUBLISH.md` — Sensitive data patterns, verification steps, publication workflow

### Source code (clean copy)
- `~/Downloads/memo-skill/README.md` — Current README with examples to sanitize
- `~/Downloads/memo-skill/scripts/` — Python/shell scripts containing vault path references
- `~/Downloads/memo-skill/.gitignore` — Current gitignore to verify .memo/ exclusion

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None in target repo (greenfield — code will be copied in)

### Established Patterns
- Clean copy at `~/Downloads/memo-skill/` has flat structure: `scripts/`, `references/`, root files
- `.gitignore` already exists in clean copy — needs verification for `.memo/` coverage

### Integration Points
- Files copy into repo root, preserving existing directory structure
- `.planning/` directory already exists in target repo — must not be overwritten

</code_context>

<specifics>
## Specific Ideas

- Author's publish instructions (`MEMO_GITHUB_PUBLISH.md`) contain a specific grep command for sensitive data — use it as the baseline scan
- Research confirmed `memo_mcp_server.py` line 147 in the INSTALLED copy has `jobhunter`/`digital-planet` — verify clean copy doesn't have this
- The `~/engineering-brain` appears exactly 9 times per research — verify count after replacement

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-security-cleanliness*
*Context gathered: 2026-04-13*
