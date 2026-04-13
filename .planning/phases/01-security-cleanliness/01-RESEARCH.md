# Phase 1: Security & Cleanliness - Research

**Researched:** 2026-04-13
**Domain:** Sensitive data sanitization, file copy workflow, git single-commit publishing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Copy files from `~/Downloads/memo-skill/` into this repo (`~/Projects/claude-memo/`). Work on the copy, not the original.
- **D-02:** Source of truth is `~/Downloads/memo-skill/` — never copy from installed copy `~/.claude/skills/memo-skill/` (confirmed to contain personal project names).
- **D-03:** Replace all occurrences of `~/engineering-brain` with `~/memo-vault` across all scripts.
- **D-04:** `MEMO_VAULT_PATH` environment variable remains the primary override mechanism — do not remove it.
- **D-05:** Replace real project/company names in README examples with generic alternatives: `JobHunter.no` → `my-saas-project`, `Finn.no`/`Webcruiter`/`Jobbnorge` → generic data source names.
- **D-06:** Preserve structure and educational value of examples — only change identifying names.
- **D-07:** Comprehensive scan covering patterns from MEMO_GITHUB_PUBLISH.md: `sergeiarutiunian`, `sk-or-v1-`, `sk-ant-api`, `@gmail`, `password`, `Dropbox/WORK`, `jobhunter`, `digital-planet`, `cookie-consent`, `Digital Planet`, `Lillestrøm`. Plus: absolute home paths (`/Users/`), API keys, tokens, email addresses. All file types: `.py`, `.sh`, `.md`, `.txt`, `.json`.
- **D-08:** After automated scan, do manual review of README examples section.
- **D-09:** Single clean commit after all sanitization is verified. No intermediate history with personal data.

### Claude's Discretion

- Exact wording of generic example replacements (as long as they're realistic and educational)
- Order of scan/replace operations
- Whether to add a pre-commit hook for sensitive data scanning (defer to Phase 2 if yes)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SEC-01 | Clean copy scanned for sensitive data (personal names, API keys, project-specific references) — zero findings | Baseline grep command from MEMO_GITHUB_PUBLISH.md verified; LICENSE file has additional finding not in baseline |
| SEC-02 | Default vault path replaced from `~/engineering-brain` to `~/memo-vault` across all scripts (9 occurrences per requirements) | Actual count is 35 occurrences across 13 files — REQUIREMENTS.md number is undercount; sed command strategy documented |
| SEC-03 | README examples genericized — no real project names (JobHunter.no, Finn.no, Webcruiter, Jobbnorge removed) | Exact lines located: README.md lines 189-190; SKILL.md line 470 has `my-saas-project` (already generic) |
| SEC-04 | `.gitignore` verified to exclude `.memo/` directory | FINDING: `.gitignore` does NOT currently contain `.memo/` — must be added |
| SEC-05 | Published repo uses single-commit workflow (no leaked history from personal development) | Target repo `~/Projects/claude-memo/` is not a git repo yet — single `git init` + commit is straightforward |
</phase_requirements>

---

## Summary

Phase 1 is a file copy + sanitize + single-commit workflow. The source files live in `~/Downloads/memo-skill/` (13 files across 3 subdirectories). The target repo at `~/Projects/claude-memo/` currently has no git history and contains only the `.planning/` directory.

Three discoveries from direct inspection that affect planning:

1. **`engineering-brain` count is 35, not 9.** The number "9" in REQUIREMENTS.md appears to be from an earlier manual count or the installed copy. The actual clean zip has 35 occurrences across 13 files (README.md, SKILL.md, scripts/\*.py, scripts/\*.sh, references/AUTO_MEMO_SETUP.md). A `sed -i` command handles all replacements in one pass.

2. **`.gitignore` is missing `.memo/`.** The current `.gitignore` only excludes `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store`, `*.egg-info/`, `dist/`, `build/`. The `.memo/` directory (containing `index.db`, `embeddings.npy`, `write.lock`, `auto_memo.log`) must be added before the initial commit to satisfy SEC-04.

3. **LICENSE file contains personal data.** `LICENSE` line 3: `Copyright (c) 2026 Sergei Arutiunian / Digital Planet AS`. This is NOT caught by the baseline grep command in MEMO_GITHUB_PUBLISH.md (which targets `sergeiarutiunian` lowercase but not `Sergei Arutiunian` with proper case, and targets `digital-planet` but not `Digital Planet AS`). The scan pattern must include `Digital Planet AS` and `Sergei Arutiunian` (mixed case), OR the LICENSE must be updated to a generic author line like `Copyright (c) 2026 claude-memo contributors`.

**Primary recommendation:** Copy files, fix .gitignore, run sed replacement for `engineering-brain` → `memo-vault`, update LICENSE to generic, replace README example names, run comprehensive scan to verify zero findings, then single `git init` + commit.

---

## Standard Stack

### Core

| Tool | Purpose | Why Standard |
|------|---------|--------------|
| `grep -rn` | Pattern scanning for sensitive data | Built-in, no dependencies, exact match + regex |
| `sed -i` | In-place text replacement | Built-in, handles multi-file replacement in one invocation |
| `git init` + `git add` + `git commit` | Single-commit workflow | Standard git, creates clean history with no personal data |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cp -r` | Copy directory tree preserving structure | File copy from Downloads to repo |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual grep | `gitleaks` / `detect-secrets` | Those tools are better for ongoing prevention (Phase 2); for a one-time audit of a clean zip, grep is sufficient and requires no installation |
| `sed` per-file | Python script | Python gives more control but adds a file; sed is sufficient for simple string replacement |

---

## Architecture Patterns

### File Copy Strategy

Copy the entire `~/Downloads/memo-skill/` tree into repo root, preserving:
```
~/Projects/claude-memo/          ← target (already has .planning/)
├── .planning/                   ← DO NOT OVERWRITE (already exists)
├── scripts/                     ← copy from source
├── references/                  ← copy from source
├── .gitignore                   ← copy from source, then ADD .memo/ entry
├── LICENSE                      ← copy from source, then update author line
├── README.md                    ← copy from source, then sanitize
├── requirements.txt             ← copy from source
└── SKILL.md                     ← copy from source, then sanitize
```

**Critical:** Use `cp` selectively or exclude `.planning/` from overwrite. The safest approach is to copy individual items rather than `cp -r source/* target/`.

### Replacement Pattern

All `engineering-brain` → `memo-vault` replacements use a single sed pass:

```bash
# Source: [VERIFIED: direct inspection of ~/Downloads/memo-skill/]
find ~/Projects/claude-memo -type f \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" \) \
  -exec sed -i '' 's|engineering-brain|memo-vault|g' {} +
```

Note: macOS `sed -i ''` (with empty string argument) is required on Darwin. Linux uses `sed -i` without the empty string.

### Scan Command (Baseline from MEMO_GITHUB_PUBLISH.md)

```bash
# Source: [VERIFIED: ~/Downloads/MEMO_GITHUB_PUBLISH.md]
grep -rn "sergeiarutiunian\|sk-or-v1-\|sk-ant-api\|@gmail\|password\|Dropbox/WORK\|jobhunter\|digital-planet\|cookie-consent\|Digital Planet\|Lillestrøm" \
  --include="*.py" --include="*.sh" --include="*.md" --include="*.txt" \
  ~/Projects/claude-memo/ \
  || echo "CLEAN — safe to publish"
```

**Extended patterns to add** (not in baseline, found by inspection):
- `Sergei Arutiunian` — in LICENSE (proper case, not caught by baseline)
- `Digital Planet AS` — in LICENSE (with "AS" suffix, baseline has `Digital Planet` without suffix — this one IS caught)
- `/Users/` — absolute home paths that could leak username

### .gitignore Addition

```
# Vault runtime data (never commit)
.memo/
```

### Git Single-Commit Workflow

```bash
# Source: [VERIFIED: ~/Downloads/MEMO_GITHUB_PUBLISH.md step 5]
cd ~/Projects/claude-memo
git init
git add -A
git commit -m "Initial release: Memo — persistent engineering memory with semantic search"
git branch -M main
```

Do NOT push in this phase (SEC-05 only requires the single commit, not publication).

### Anti-Patterns to Avoid

- **Copying from the installed copy:** `~/.claude/skills/memo-skill/` contains `jobhunter`/`digital-planet` references. Always use `~/Downloads/memo-skill/`.
- **Committing before scan passes:** The scan is a gate, not an afterthought.
- **`git add -A` before .gitignore is updated:** If the target machine has a `.memo/` dir in the repo root and `.gitignore` is not yet updated, sensitive vault data could be staged. Update `.gitignore` before any `git add`.
- **Overwriting `.planning/`:** The planning directory exists and must not be touched by the copy operation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sensitive data scan | Custom Python scanner | `grep -rn` with pattern list | Grep is deterministic, readable, and the exact command is already documented in MEMO_GITHUB_PUBLISH.md |
| Multi-file text replacement | Python replace script | `sed -i` + `find` | One-liner, no new file, handles all 35 occurrences in one pass |

---

## Runtime State Inventory

> Skipped — this is a greenfield copy+sanitize phase. No existing git history, no running services, no stored data in the target repo to rename.

---

## Common Pitfalls

### Pitfall 1: engineering-brain Count Mismatch

**What goes wrong:** Requirements say "9 occurrences" but actual count in clean zip is 35. If the plan says "verify 9 replacements" the verification step will incorrectly report success.

**Why it happens:** The "9" was likely an early manual count from a different file set (possibly only scripts/, not README.md/SKILL.md/references/).

**How to avoid:** After replacement, verify with `grep -rn "engineering-brain"` returns zero results. Do not gate on a count of 9.

**Warning signs:** If post-replacement grep still finds matches, some file type was missed in the find command.

### Pitfall 2: .gitignore Missing .memo/

**What goes wrong:** Developer copies files, runs git init, does git add -A — if user has a `.memo/` directory in the vault path (which defaults to `~/memo-vault` after replacement, not repo root), it's not in the repo anyway. BUT if the vault path were ever set to the repo itself, vault data would be committed.

**Why it happens:** The `.gitignore` in the clean zip was never updated to include `.memo/`. SEC-04 explicitly requires this.

**How to avoid:** Add `.memo/` to `.gitignore` immediately after copying the file, before any git operations.

### Pitfall 3: LICENSE Personal Data Not in Baseline Scan

**What goes wrong:** Running only the MEMO_GITHUB_PUBLISH.md grep command gives a false CLEAN result because the LICENSE file contains `Sergei Arutiunian / Digital Planet AS`. The baseline catches `Digital Planet` but would match it — let's verify: `Digital Planet` IS in the baseline pattern `Digital Planet`. `Sergei Arutiunian` has proper case but `sergeiarutiunian` is lowercase-only. The grep baseline will NOT catch `Sergei Arutiunian`.

**Why it happens:** The baseline scan pattern uses lowercase `sergeiarutiunian` — case-sensitive grep misses `Sergei Arutiunian`.

**How to avoid:** Either add `-i` flag (case-insensitive) to the scan, or add `Sergei` to the pattern list, or update LICENSE to a generic contributor line before scanning.

**Warning signs:** grep returns CLEAN but LICENSE still has real name in it.

### Pitfall 4: macOS sed Syntax

**What goes wrong:** `sed -i 's/old/new/g' file` fails on macOS with "invalid command code" error.

**Why it happens:** BSD sed (macOS) requires an extension argument after `-i`. GNU sed (Linux) does not.

**How to avoid:** Always use `sed -i '' 's/old/new/g' file` on macOS (Darwin).

### Pitfall 5: .planning/ Overwrite

**What goes wrong:** `cp -r ~/Downloads/memo-skill/. ~/Projects/claude-memo/` could theoretically overwrite files if the source somehow had a `.planning/` directory.

**Why it happens:** Careless wildcard copy.

**How to avoid:** The clean zip does not contain `.planning/` (verified: its structure is `scripts/`, `references/`, and root files only). But copy selectively anyway: copy named items explicitly or use `rsync --exclude='.planning'`.

---

## Code Examples

### Full Sanitization Sequence (Verified Pattern)

```bash
# Step 1: Copy files from clean zip to repo (excluding .planning/)
# Source: [VERIFIED: direct inspection of ~/Downloads/memo-skill/ structure]
cp -r ~/Downloads/memo-skill/scripts ~/Projects/claude-memo/
cp -r ~/Downloads/memo-skill/references ~/Projects/claude-memo/
cp ~/Downloads/memo-skill/{README.md,SKILL.md,requirements.txt,LICENSE,.gitignore} ~/Projects/claude-memo/

# Step 2: Add .memo/ to .gitignore (SEC-04)
echo "" >> ~/Projects/claude-memo/.gitignore
echo "# Vault runtime data (never commit)" >> ~/Projects/claude-memo/.gitignore
echo ".memo/" >> ~/Projects/claude-memo/.gitignore

# Step 3: Replace engineering-brain → memo-vault (SEC-02)
# macOS syntax: sed -i '' (empty string required)
find ~/Projects/claude-memo -not -path "*/.planning/*" -type f \
  \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" \) \
  -exec sed -i '' 's|engineering-brain|memo-vault|g' {} +

# Step 4: Update LICENSE personal data
# Change: Copyright (c) 2026 Sergei Arutiunian / Digital Planet AS
# To: Copyright (c) 2026 claude-memo contributors
sed -i '' 's|Sergei Arutiunian / Digital Planet AS|claude-memo contributors|g' ~/Projects/claude-memo/LICENSE

# Step 5: Update README example project names (SEC-03)
# Target: README.md lines 189-190
# JobHunter.no → my-saas-project
# Finn.no, Webcruiter, Jobbnorge → generic-jobs-api, careers-api, jobboard-api
sed -i '' 's|JobHunter\.no|my-saas-project|g; s|Finn\.no|generic-jobs-api|g; s|Webcruiter|careers-api|g; s|Jobbnorge|jobboard-api|g' ~/Projects/claude-memo/README.md

# Step 6: Run comprehensive scan (SEC-01)
# Extended pattern includes Sergei (proper case) and /Users/ paths
grep -rni "sergeiarutiunian\|sergei arutiunian\|sk-or-v1-\|sk-ant-api\|@gmail\|password\|Dropbox/WORK\|jobhunter\|digital-planet\|digital planet\|cookie-consent\|Lillestrøm\|/Users/" \
  --include="*.py" --include="*.sh" --include="*.md" --include="*.txt" --include="*.json" \
  ~/Projects/claude-memo/ \
  || echo "CLEAN — safe to publish"

# Step 7: Verify engineering-brain is fully gone
grep -rn "engineering-brain" ~/Projects/claude-memo/ && echo "FOUND — fix before committing" || echo "CLEAN"

# Step 8: Manual check of README examples section (D-08)
# Human reads lines around "JobHunter" context to confirm no residual personal refs

# Step 9: Single clean commit (SEC-05)
cd ~/Projects/claude-memo
git init
git add -A
git commit -m "Initial release: Memo — persistent engineering memory with semantic search"
git branch -M main
```

### Verify .gitignore Coverage (SEC-04)

```bash
# Source: [VERIFIED: read of ~/Downloads/memo-skill/.gitignore]
# Current .gitignore does NOT have .memo/ — must add it
grep ".memo" ~/Projects/claude-memo/.gitignore || echo "MISSING — add .memo/ entry"
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Manual per-file editing | `sed` + `find` bulk replacement | All 35 occurrences replaced reliably in one command |
| Copying from installed skill | Copying from clean zip | Avoids project-specific contamination confirmed in installed copy |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `~/Projects/claude-memo/` is not yet a git repo (git init required) | Code Examples | If repo already initialized, `git init` is a no-op — low risk |
| A2 | `SKILL.md` line 470 `my-saas-project` is already generic and does not need replacement | Phase Requirements | If `my-saas-project` is itself a real project name, it stays — but context shows it's clearly fictional |
| A3 | No `.memo/` directory exists in the target repo at execution time | Common Pitfalls | If user has created a local vault there, git add -A without .gitignore fix could stage vault data |

---

## Open Questions

1. **LICENSE author line: update or leave?**
   - What we know: `Copyright (c) 2026 Sergei Arutiunian / Digital Planet AS` is in LICENSE. `Digital Planet` IS caught by the baseline scan (case-sensitive, exact). `Sergei Arutiunian` (proper case) is NOT caught by `sergeiarutiunian` (lowercase-only) in the baseline.
   - What's unclear: User intent — personal attribution in MIT license vs. generic author.
   - Recommendation: Replace with `claude-memo contributors` or `Sergei Arutiunian` if the user wants personal attribution (MIT license with real name is standard practice and not harmful per se). The security issue is only if the name + company is considered sensitive. Planner should add a task to confirm user preference.

2. **`engineering-brain` in SKILL.md (5 occurrences) — SKILL.md ships with the repo?**
   - What we know: SKILL.md is at repo root and contains `engineering-brain` 5 times.
   - What's unclear: SKILL.md is a Claude Code skill index — it's meant to be read by Claude. It should also be sanitized.
   - Recommendation: Include SKILL.md in the sed replacement pass. Already included in the find command above.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `grep` | SEC-01 scan | yes | built-in BSD grep | — |
| `sed` | SEC-02 replacement | yes | BSD sed (macOS, requires `''`) | — |
| `find` | File traversal | yes | built-in | — |
| `git` | SEC-05 single commit | yes | built-in on macOS | — |
| `cp` | File copy | yes | built-in | — |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

> No test framework required for this phase. Validation is grep-based: scan returns zero findings = pass.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| SEC-01 | Zero sensitive data findings in scan | smoke | `grep -rni "sergeiarutiunian\|sergei arutiunian\|sk-or-v1-\|..." ~/Projects/claude-memo/ && echo FAIL \|\| echo PASS` |
| SEC-02 | Zero `engineering-brain` occurrences remain | smoke | `grep -rn "engineering-brain" ~/Projects/claude-memo/ && echo FAIL \|\| echo PASS` |
| SEC-03 | Zero real project names in README | smoke | `grep -n "JobHunter\|Finn\.no\|Webcruiter\|Jobbnorge" ~/Projects/claude-memo/README.md && echo FAIL \|\| echo PASS` |
| SEC-04 | `.gitignore` contains `.memo/` | smoke | `grep ".memo" ~/Projects/claude-memo/.gitignore \|\| echo FAIL` |
| SEC-05 | Single commit in git log | smoke | `git -C ~/Projects/claude-memo log --oneline \| wc -l` should equal 1 |

### Wave 0 Gaps

None — no test framework needed; all validation is shell commands.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Note |
|---------------|---------|------|
| V2 Authentication | no | No auth in this phase |
| V5 Input Validation | no | No user input in this phase |
| V6 Cryptography | no | No crypto in this phase |
| Secret/PII Exposure (pre-publish audit) | YES | Core of this phase — prevent PII and API keys from entering git history |

### Threat: Sensitive Data in Initial Commit

| Pattern | Risk | Mitigation |
|---------|------|------------|
| Personal name in LICENSE | Low (MIT license attribution is normal) | Confirm with user; replace if desired |
| Real project names in README examples | Medium (leaks client/employer info) | Replace with generic names per D-05 |
| `engineering-brain` path | Low (neutral path name, but personal) | Replace with `memo-vault` per D-03 |
| Installed copy contamination | High (confirmed `jobhunter`/`digital-planet`) | Use only clean zip source per D-02 |

**Key principle:** Git history is permanent. The scan gate (Step 6 above) must return zero findings before `git add`. There is no "fix it later" once history exists.

---

## Sources

### Primary (HIGH confidence)
- `~/Downloads/MEMO_GITHUB_PUBLISH.md` — Official author-written baseline scan command and publication workflow [VERIFIED: read directly]
- `~/Downloads/memo-skill/` directory — Direct inspection of all files and grep counts [VERIFIED: grep + ls commands]
- `~/Downloads/memo-skill/.gitignore` — Confirmed missing `.memo/` entry [VERIFIED: file read]
- `~/Projects/claude-memo/CLAUDE.md` — Project constraints and stack decisions [VERIFIED: file read]

### Secondary (MEDIUM confidence)
- macOS `sed -i ''` syntax requirement [ASSUMED: macOS-specific, well-known BSD vs GNU difference]

---

## Metadata

**Confidence breakdown:**
- Scan patterns: HIGH — verified against actual file contents
- engineering-brain count (35 vs stated 9): HIGH — verified by grep
- .gitignore gap: HIGH — verified by file read
- LICENSE personal data gap: HIGH — verified by grep
- macOS sed syntax: HIGH — standard macOS behavior

**Research date:** 2026-04-13
**Valid until:** Indefinite (file contents won't change; this is a one-time operation)
