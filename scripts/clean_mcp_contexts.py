#!/usr/bin/env python3
"""Utilities to clean local MCP session contexts (.mcp_contexts/).

Usage examples:
  - Delete everything:      python scripts/clean_mcp_contexts.py --all
  - Prune older than 7 days: python scripts/clean_mcp_contexts.py --days 7
  - Dry run preview:         python scripts/clean_mcp_contexts.py --days 7 --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path


def resolve_repo_root() -> Path:
    this_file = Path(__file__).resolve()
    return this_file.parent.parent


def delete_all(context_dir: Path, dry_run: bool) -> int:
    if not context_dir.exists():
        print(f"No directory to clean: {context_dir}")
        return 0

    total_removed = 0
    for entry in context_dir.iterdir():
        if dry_run:
            print(f"DRY-RUN would remove: {entry}")
            total_removed += 1
            continue
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            try:
                entry.unlink(missing_ok=True)  # py3.8+ compatible via try/except if needed
            except TypeError:
                # Fallback for very old Python versions
                try:
                    entry.unlink()
                except FileNotFoundError:
                    pass
        total_removed += 1
    return total_removed


def prune_older_than_days(context_dir: Path, days: int, dry_run: bool) -> int:
    if not context_dir.exists():
        print(f"No directory to prune: {context_dir}")
        return 0

    cutoff_seconds = time.time() - (days * 24 * 60 * 60)
    total_removed = 0

    for root, dirs, files in os.walk(context_dir):
        root_path = Path(root)
        for name in files:
            file_path = root_path / name
            try:
                mtime = file_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if mtime < cutoff_seconds:
                if dry_run:
                    print(f"DRY-RUN would remove: {file_path}")
                else:
                    try:
                        file_path.unlink()
                    except FileNotFoundError:
                        pass
                total_removed += 1

        # Optionally remove empty directories after file pruning
        for name in list(dirs):
            dir_path = root_path / name
            try:
                is_empty = not any(dir_path.iterdir())
            except FileNotFoundError:
                is_empty = False
            if is_empty:
                if dry_run:
                    print(f"DRY-RUN would remove empty dir: {dir_path}")
                else:
                    shutil.rmtree(dir_path, ignore_errors=True)
                total_removed += 1

    return total_removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean or prune .mcp_contexts cache directory")
    parser.add_argument("--all", action="store_true", help="Delete all contents in .mcp_contexts/")
    parser.add_argument("--days", type=int, default=7, help="Prune files older than N days (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")
    args = parser.parse_args(argv)

    repo_root = resolve_repo_root()
    context_dir = repo_root / ".mcp_contexts"

    if args.all:
        removed = delete_all(context_dir, args.dry_run)
        print(f"Removed entries: {removed}")
        return 0

    removed = prune_older_than_days(context_dir, args.days, args.dry_run)
    print(f"Pruned entries older than {args.days} days: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


