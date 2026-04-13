# Phase 1: Security & Cleanliness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 01-security-cleanliness
**Areas discussed:** Source handling, Vault path naming, Example content, Scan scope
**Mode:** --auto (all decisions auto-selected with recommended defaults)

---

## Source handling

| Option | Description | Selected |
|--------|-------------|----------|
| Copy into this repo | Work on copy in ~/Projects/claude-memo/ | ✓ |
| Work in Downloads | Edit clean copy in place | |

**User's choice:** [auto] Copy into this repo (recommended default)
**Notes:** Target repo is the GSD project directory; Downloads copy remains untouched as backup.

---

## Vault path naming

| Option | Description | Selected |
|--------|-------------|----------|
| ~/memo-vault | Neutral, descriptive default | ✓ |
| ~/engineering-brain | Keep original (personal) | |
| ~/knowledge-vault | Alternative neutral name | |

**User's choice:** [auto] ~/memo-vault (recommended by research)
**Notes:** Research identified 9 occurrences to replace.

---

## Example content

| Option | Description | Selected |
|--------|-------------|----------|
| Generic examples | Replace with fictional but realistic names | ✓ |
| Remove examples | Strip examples entirely | |

**User's choice:** [auto] Generic examples (recommended default)
**Notes:** Preserve example structure, only change identifying names.

---

## Scan scope

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive | MEMO_GITHUB_PUBLISH.md patterns + additional common patterns | ✓ |
| Minimal | Only patterns from publish doc | |

**User's choice:** [auto] Comprehensive (recommended default)
**Notes:** Includes absolute paths, API key patterns, email addresses beyond the base list.

---

## Claude's Discretion

- Exact wording of generic example replacements
- Order of scan/replace operations
- Pre-commit hook for sensitive data (deferred to Phase 2)

## Deferred Ideas

None
