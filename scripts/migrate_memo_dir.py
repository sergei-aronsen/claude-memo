#!/usr/bin/env python3
"""
migrate_memo_dir.py — Move legacy <vault>/.memo/ to ~/.cache/memo/<hash>/.

Architectural fix: the per-machine cache (SQLite index, embeddings,
logs, lock files, debug captures) used to live inside the vault.
That made Dropbox / iCloud sync them, which produced:

  - SQLite WAL conflicts → "disk image malformed" errors
  - Cross-machine races flock could not coordinate
  - Bandwidth waste (logs grew unbounded inside a synced folder)
  - Privacy leak (auto_memo.log + hook_payloads.jsonl in backup)

The vault itself (markdown files) is unchanged — that IS the
knowledge and DOES belong in sync.

Usage:
  python3 scripts/migrate_memo_dir.py --vault /path/to/vault [--dry-run]

The migration is also triggered automatically on the next hook /
engine call — this script is only here for users who want to run
it explicitly first, see the diff, and confirm.
"""

import argparse
import os
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", required=True, help="Path to vault root")
    parser.add_argument("--dry-run", action="store_true", help="Print actions, do not move files")
    parser.add_argument("--force", action="store_true", help="Migrate even if cache already has index files")
    args = parser.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from memo_utils import _vault_hash, get_memo_dir

    vault = os.path.expanduser(args.vault)
    if not os.path.isdir(vault):
        print(f"ERROR: vault does not exist: {vault}", file=sys.stderr)
        sys.exit(1)

    legacy = os.path.join(vault, ".memo")
    breadcrumb = os.path.join(vault, ".memo.migrated-to-cache")
    cache_dir = os.path.join(os.path.expanduser("~/.cache/memo"), _vault_hash(vault))

    print(f"vault:     {vault}")
    print(f"legacy:    {legacy}")
    print(f"cache:     {cache_dir}")
    print(f"breadcrumb {'exists' if os.path.exists(breadcrumb) else 'missing'}: {breadcrumb}")

    if os.path.exists(breadcrumb) and not args.force:
        print("Already migrated (breadcrumb present). Use --force to re-run.")
        sys.exit(0)

    if not os.path.isdir(legacy):
        print("No legacy .memo/ directory in vault — nothing to migrate.")
        # Still ensure cache dir exists.
        if not args.dry_run:
            get_memo_dir(vault)
        sys.exit(0)

    legacy_contents = os.listdir(legacy)
    if not legacy_contents:
        print("Legacy .memo/ is empty.")
        if not args.dry_run:
            try:
                os.rmdir(legacy)
            except OSError:
                pass
        sys.exit(0)

    if not args.dry_run:
        os.makedirs(cache_dir, exist_ok=True)
        try:
            os.chmod(cache_dir, 0o700)
        except OSError:
            pass

    cache_existing = set(os.listdir(cache_dir)) if os.path.isdir(cache_dir) else set()
    danger = {name for name in ("index.db", "embeddings.npy", "id_map.json") if name in cache_existing}
    if danger and not args.force:
        print(f"REFUSE: cache already contains {sorted(danger)}. Pass --force to overwrite.", file=sys.stderr)
        sys.exit(2)

    print("\nFiles to move:")
    for name in sorted(legacy_contents):
        src = os.path.join(legacy, name)
        dst = os.path.join(cache_dir, name)
        kind = "dir" if os.path.isdir(src) else "file"
        print(f"  {kind:4s}  {src}  →  {dst}")

    if args.dry_run:
        print("\n(dry-run — no files moved)")
        sys.exit(0)

    moved = 0
    for name in legacy_contents:
        src = os.path.join(legacy, name)
        dst = os.path.join(cache_dir, name)
        try:
            if os.path.isdir(src):
                if os.path.isdir(dst):
                    for sub in os.listdir(src):
                        try:
                            shutil.move(os.path.join(src, sub), os.path.join(dst, sub))
                        except (OSError, shutil.Error) as e:
                            print(f"  skip {os.path.join(src, sub)}: {e}", file=sys.stderr)
                    try:
                        os.rmdir(src)
                    except OSError:
                        pass
                else:
                    shutil.move(src, dst)
            else:
                shutil.move(src, dst)
            moved += 1
        except (OSError, shutil.Error) as e:
            print(f"  skip {src}: {e}", file=sys.stderr)

    try:
        with open(breadcrumb, "w", encoding="utf-8") as f:
            f.write(
                "This vault used to have a `.memo/` directory inside it.\n"
                f"Contents have been moved to: {cache_dir}\n"
                "This file is a breadcrumb so the migration is not repeated.\n"
                "Safe to delete this file once you have confirmed the cache works.\n"
            )
    except OSError as e:
        print(f"WARN: could not write breadcrumb: {e}", file=sys.stderr)

    try:
        if not os.listdir(legacy):
            os.rmdir(legacy)
    except OSError:
        pass

    print(f"\nDone. Moved {moved} entries. Cache: {cache_dir}")


if __name__ == "__main__":
    main()
