# Domain Pitfalls: Open-Sourcing a Personal AI Tool

**Domain:** Personal developer tool → public GitHub repository
**Project:** claude-memo
**Researched:** 2026-04-13
**Confidence:** HIGH (code inspected directly; pitfalls confirmed in actual files)

---

## Critical Pitfalls

Mistakes that cause rewrites, security incidents, or permanently kill adoption.

---

### Pitfall 1: Publishing the Installed Copy Instead of the Clean Copy

**What goes wrong:** The installed copy at `~/.claude/skills/memo-skill/` diverges from the clean copy over time. Real project names appear in docstrings, comments, and example snippets as the tool is used in production. One confirmed difference already exists: `memo_mcp_server.py` line 147 uses real client project names (`jobhunter`, `digital-planet`) as examples in the installed copy, while the clean copy uses `my-saas`, `client-website`.

**Why it happens:** The author edits code in place while using it. The diff between clean and installed accumulates silently. "Just push what's installed" is the path of least resistance.

**Consequences:** Real project names become permanent in git history. Google indexes them. Even after deletion, the Wayback Machine and GitHub Archive retain the original commit. 64% of leaked data from 2022 was still accessible online in 2025.

**Warning signs:**
- Docstring examples reference specific domain names, not generic placeholders
- Comments say things like "used for my X project" rather than "e.g., my-saas"
- `grep` finds any word in the publish instructions' sensitive-data checklist

**Prevention:**
- Always publish from `~/Downloads/memo-skill/` (the designated clean copy), never from `~/.claude/skills/memo-skill/`
- Run the sensitive-data grep from MEMO_GITHUB_PUBLISH.md before every push: `grep -rn "sergeiarutiunian|sk-or-v1-|sk-ant-api|@gmail|Dropbox/WORK|jobhunter|digital-planet|cookie-consent|Lillestrøm"`
- Add these real project names to a pre-commit hook so they can never accidentally slip through

**Phase:** Must be addressed in the "Prepare & Verify" phase, before `git init`.

---

### Pitfall 2: Sensitive Data Buried in Git History

**What goes wrong:** Even if the published files are clean, the git history may contain prior versions with personal data. Once a repo is made public, GitHub Archive and web crawlers index it within minutes. Deleting the file in a subsequent commit does NOT remove it from history — the data remains accessible via `git log -p` or GitHub's commit diff view.

**Why it happens:** The publish instructions call for `git init` and a single initial commit from the clean directory. This is correct *if done exactly*. The risk is if any intermediate commits exist (e.g., testing, partial pushes) before the repo goes public.

**Consequences:** Anthropic API keys (`sk-ant-*`) and OpenRouter keys (`sk-or-v1-*`) can be rotated, but the exposure window is unknown and may trigger automated scanners within seconds. GitGuardian and GitHub's own secret scanning alert on these patterns in real-time.

**Warning signs:**
- The repo has more than one commit before going public
- Any local git history exists in the release directory before the initial push

**Prevention:**
- Use exactly the workflow from MEMO_GITHUB_PUBLISH.md: `rm -rf ~/memo-skill-release`, fresh `git init`, single commit, then publish
- Never push a private repo first and then make it public — this preserves all prior history
- If using a fresh `git init`, there is only one commit, eliminating history risk entirely

**Phase:** Pre-publish verification, before `git remote add origin`.

---

### Pitfall 3: `__pycache__` and `.pyc` Files Committed

**What goes wrong:** The installed copy contains `__pycache__/` with compiled `.pyc` bytecode. Bytecode can embed absolute paths from the build machine. Compiled Python files have been shown to contain secrets (the 2024 PyPI token leak occurred via a `.pyc` file in a Docker image). Path information like `/Users/sergeiarutiunian/` becomes permanently embedded.

**Why it happens:** The current `.gitignore` in the clean copy correctly lists `__pycache__/` and `*.pyc`. However, if files are already tracked (e.g., from a prior git session) or the gitignore is bypassed, these files slip through.

**Warning signs:**
- `git status` shows any `.pyc` or `__pycache__/` entries
- The `.gitignore` is not committed as the first file

**Prevention:**
- Confirm the `.gitignore` is present and correct before `git add -A`
- Run `find . -name "*.pyc" -o -name "__pycache__"` in the release directory and verify zero results before committing
- The clean copy's `.gitignore` correctly handles this, but the check must be explicit

**Phase:** Pre-publish, part of the verification step.

---

### Pitfall 4: SQLite Index File Accidentally Committed

**What goes wrong:** The `.memo/` directory contains `index.db` (SQLite with FTS5), `embeddings.npy` (numpy vectors), and `auto_memo.log`. These are runtime artifacts derived from the author's actual vault content. If committed, they expose the content of every note ever captured — the exact private engineering knowledge the tool is designed to store.

**Why it happens:** The `.memo/` directory is correctly gitignored in the vault's own `.gitignore` (the one `init_vault.sh` creates inside `~/engineering-brain/.gitignore`). But this is a different `.gitignore` from the one in the skill repo itself. If the skill ever runs from within a git-tracked directory, or if `MEMO_VAULT_PATH` points to a directory that is the git root, the index files could be staged.

**Warning signs:**
- The skill repo's own `.gitignore` does not exclude `*.db`, `*.npy`, `*.log`
- `git status` shows any files from `.memo/` in the staging area

**Prevention:**
- Verify that the skill repo's `.gitignore` (currently only covering `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store`, `*.egg-info/`, `dist/`, `build/`) is sufficient for the repository being published
- The skill directory and the vault directory are separate by design — confirm this separation is clear in documentation

**Phase:** Pre-publish verification.

---

## Moderate Pitfalls

Mistakes that hurt adoption, confuse users, or cause first-run failures.

---

### Pitfall 5: `~/engineering-brain` as Default Vault Path in Code

**What goes wrong:** Nine places in the scripts use `~/engineering-brain` as a hardcoded default or example. This is the author's personal vault name, not a generic placeholder. New users who follow Quick Start without reading carefully will have their vault named `engineering-brain`, which is a personal branding choice, not a neutral default like `~/memo-vault` or `~/knowledge-vault`.

**Why it happens:** The name was chosen for the author's own use and propagated throughout the codebase. The defaults are technically overridable via `MEMO_VAULT_PATH` and command-line arguments, but the name appears in documentation, commit messages generated by `init_vault.sh`, and the MCP server example configs.

**Consequences:** Not a security issue, but a friction/credibility issue. Users who clone the repo see `engineering-brain` everywhere and either adopt the author's naming convention or must hunt down all nine occurrences to change it. It signals "personal project, not a polished tool."

**Warning signs:**
- `grep -r "engineering-brain" scripts/` returns more than 0 results in README examples
- The vault name appears in auto-generated git commit messages (see `init_vault.sh` line 182)

**Prevention strategy options (choose one):**
- Replace `~/engineering-brain` with `~/memo-vault` as the neutral default throughout all scripts and README examples — one find-and-replace, low risk
- Alternatively, make the default truly dynamic: prompt the user for a vault name during `init_vault.sh` setup

**Phase:** Pre-publish cleanup or the first post-publish patch.

---

### Pitfall 6: First-Run Silent Failure When MEMO_VAULT_PATH Is Not Set

**What goes wrong:** `save_raw_log.py` line 99 has a fallback to `os.path.expanduser("~/engineering-brain")` with no environment variable check — the code silently uses this path if `MEMO_VAULT_PATH` is unset. The SessionEnd hook fires immediately on first install, before the user has run `init_vault.sh`. The script tries to write to a non-existent directory, fails silently (or logs to nowhere), and the user sees no error but loses session data.

**Why it happens:** The hook runs as a background subprocess. Any exception gets swallowed unless the user knows to check `~/.memo/auto_memo.log`. New users will not know where to look.

**Warning signs:**
- `save_raw_log.py` writes to a hardcoded path without checking if the directory exists
- The hook runs silently with no user feedback on first use

**Prevention:**
- Add an explicit check in `save_raw_log.py`: if vault directory does not exist and `MEMO_VAULT_PATH` is not set, write a clear error to stderr and exit with code 1 so Claude Code surfaces it
- Document in README that `MEMO_VAULT_PATH` must be set (or `init_vault.sh` must be run) before hooks are activated
- Consider a `memo doctor` command that validates the setup

**Phase:** README/documentation phase or a quick code hardening pass.

---

### Pitfall 7: 1.1 GB Model Download With No User Warning

**What goes wrong:** The first call to `get_model()` in `memo_engine.py` triggers a 1.1 GB download from Hugging Face. The README mentions this in the Requirements section, but the Quick Start step `python3 memo_engine.py warm-up` executes it without confirmation. On a metered connection or corporate network with egress restrictions, this silently consumes bandwidth or fails mid-download.

**Why it happens:** The `SentenceTransformer` constructor downloads on first use. There is no progress bar, no size warning, no cancellation path in the warm-up command.

**Consequences:** Users on slow connections see what appears to be a hanging process. Users on restricted networks get an SSL or firewall error with no guidance. This is one of the highest-friction points in the install flow and directly impacts adoption.

**Warning signs:**
- The `warm-up` command output provides no download progress feedback
- No size warning appears before the download starts

**Prevention:**
- In `memo_engine.py warm-up`, print the model name and approximate size before calling `get_model()`: "Downloading intfloat/multilingual-e5-large (~1.1GB) from Hugging Face..."
- The `sentence-transformers` library shows a tqdm progress bar by default if tqdm is installed — add it to `requirements.txt`
- Document in README that the warm-up step requires internet access and ~1.1GB disk space (currently partially documented)

**Phase:** First-run UX improvement, can be done at any time post-publish.

---

### Pitfall 8: Requirements File Lacks Version Pins

**What goes wrong:** `requirements.txt` lists dependencies without pinned versions. `sentence-transformers` is an actively developed library — breaking changes between major versions (e.g., the v3.0 API changes around model loading) have affected users. `numpy` v2.x introduced breaking changes for code using `np.bool` and similar removed aliases.

**Why it happens:** The tool was built for personal use where the author controls the environment. Version pinning is defensive infrastructure that matters when others install it.

**Consequences:** A user installing on the day a new `sentence-transformers` version drops may get a different API, different model behavior, or outright import errors. The project gets GitHub issues saying "doesn't work" with no reproducible environment.

**Prevention:**
- At minimum, pin major versions in `requirements.txt`
- Better: provide a `requirements-lock.txt` with exact versions from the author's working environment
- Document tested Python version (currently stated as 3.10+ but not pinned in `pyproject.toml` or `setup.cfg`)

**Phase:** Pre-publish or first post-publish patch.

---

## Minor Pitfalls

Issues that cause confusion but are easy to recover from.

---

### Pitfall 9: README Example Note Contains Real Project Name

**What goes wrong:** The README's "Note format" example (line 189-212) references `JobHunter.no`, a real project. This is inside a code block and clearly labeled as an example, so it is not a security risk. However, it reveals the author's actual project domain, which some users may recognize.

**Prevention:** Replace `JobHunter.no` with a generic `my-api-project.com` and `Finn.no`/`Webcruiter`/`Jobbnorge` with `DataSourceA`/`DataSourceB`/`DataSourceC`. Already partially done in the clean copy (README has this example) — verify it is truly generic before publish.

**Phase:** Final review pass before publish.

---

### Pitfall 10: MCP Server Setup Instructions Reference Incorrect Claude Desktop Config Path

**What goes wrong:** The MCP server documentation shows a `claude_desktop_config.json` path. This path differs between macOS, Linux, and Windows. The README currently targets macOS (`~/Library/Application Support/Claude/`). Users on Linux who follow these instructions will set up the config in the wrong location.

**Prevention:** Show platform-specific paths or reference the official Claude Desktop documentation for the correct path per OS.

**Phase:** Documentation improvement, low urgency.

---

### Pitfall 11: Vault `.obsidian/` Config Committed to the Skill Repo

**What goes wrong:** `init_vault.sh` creates `.obsidian/app.json`, `graph.json`, `plugins/`, and other Obsidian configuration files inside the vault. These are user-specific and will diverge immediately after first use. If any user creates a PR or forks the repo and accidentally includes their vault path in these configs, it leaks personal data in a non-obvious location.

**Why this matters for the skill repo specifically:** The skill repo itself does not contain vault files, so this is a documentation risk rather than a code risk. But the install instructions send users to a path that mixes the skill code (`~/.claude/skills/memo-skill/`) with their vault (`~/engineering-brain/`). Users who misread the setup may add their vault to the skill repo's git tracking.

**Prevention:** Make explicit in README that the vault directory is entirely separate from the skill directory and should never be inside the skill's git repo.

**Phase:** README clarity improvement.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Preparing the release directory | Using installed copy instead of clean copy | Always work from `~/Downloads/memo-skill/` |
| Running sensitive data grep | Incomplete grep pattern missing new project names | Add names as they appear; grep is the last line of defense |
| `git init` and first commit | Intermediate commits before making repo public | Single commit workflow only |
| README final review | Real project names in code examples (`JobHunter.no`) | Replace with generic names |
| Dependency declaration | Unpinned versions breaking on new installs | Pin at minimum major versions |
| Post-publish first issues | Users confused by 1.1GB download hanging silently | Add progress output and size warning |
| Post-publish install flow | `save_raw_log.py` silent failure before vault init | Add guard clause and error message |

---

## Sources

- Direct code inspection: `/Users/sergeiarutiunian/Downloads/memo-skill/scripts/` (clean copy)
- Direct code inspection: `/Users/sergeiarutiunian/.claude/skills/memo-skill/scripts/` (installed copy)
- MEMO_GITHUB_PUBLISH.md — author's own checklist, reveals known sensitive project names
- [GitGuardian: Why devs and repos spill secrets](https://www.reversinglabs.com/blog/secrets-exposed-modern-development-open-source-repositories-expose-secrets-en-masse)
- [Python PyPI token leak via .pyc file (2024)](https://blog.pypi.org/posts/2024-07-08-incident-report-leaked-admin-personal-access-token/)
- [How to Remove Sensitive Data from Git — Sparkbox](https://sparkbox.com/foundry/remove_file_from_git_history_with_git_filter-branch)
- [MCP Credential Exposure Risks](https://cyata.ai/blog/whispering-secrets-loudly-inside-mcps-quiet-crisis-of-credential-exposure/)
- [Python .gitignore best practices — Python Central](https://www.pythoncentral.io/python-gitignore-clean-repository-management/)
