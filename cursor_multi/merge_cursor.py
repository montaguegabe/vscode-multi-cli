#!/usr/bin/env python3

import os
import sys
from typing import List

from .utils import load_repos, get_git_root
from .rules import cleanup_old_imported_rules, import_cursor_rules


def main():
    print("🔄 Merging Cursor rules...")
    git_root = get_git_root()

    # Get repo names from repos.json
    repos = load_repos()
    repo_names = [repo_url.split("/")[-1] for repo_url in repos]

    # Clean up any previously imported rules
    print("\n🔄 Cleaning up old imported rules...")
    cleanup_old_imported_rules(git_root)

    # Import cursor rules from each repository
    print("\n🔄 Importing Cursor rules...")
    imported_rules = import_cursor_rules(git_root, repo_names)

    # Update .gitignore and .ignore with repo names and imported rules
    from .setup import update_ignore_files

    update_ignore_files(repo_names, imported_rules)

    print("\n✨ Cursor rules merged successfully!")


if __name__ == "__main__":
    main()
