#!/usr/bin/env python3

import argparse
import os
import sys
from typing import List

from .utils import load_repos, run_git, validate_git_repo, check_branch_existence


def create_and_switch_branch(repo_path: str, branch_name: str) -> bool:
    """Create a branch if it doesn't exist and switch to it."""
    try:
        if not validate_git_repo(repo_path):
            return False

        # Get current branch
        current = run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], "get current branch", repo_path
        )
        current_branch = current.stdout.strip()

        # If we're already on the target branch, no need to do anything
        if current_branch == branch_name:
            print(f"✅ Already on branch '{branch_name}' in {repo_path}")
            return True

        # Check if branch exists locally or remotely
        exists_locally, exists_remotely = check_branch_existence(repo_path, branch_name)

        if exists_locally or exists_remotely:
            print(f"Branch '{branch_name}' already exists in {repo_path}")
            if exists_remotely:
                try:
                    # If it exists remotely, check it out and track it
                    run_git(
                        ["checkout", branch_name], "checkout existing branch", repo_path
                    )
                    # Update the branch to match remote
                    run_git(
                        ["reset", "--hard", f"origin/{branch_name}"],
                        "reset to remote branch",
                        repo_path,
                    )
                except Exception as e:
                    print(
                        f"\n❌ Failed to checkout remote branch in {repo_path}: {str(e)}"
                    )
                    return False
            else:
                try:
                    # If it only exists locally, just check it out
                    run_git(
                        ["checkout", branch_name], "checkout existing branch", repo_path
                    )
                except Exception as e:
                    print(
                        f"\n❌ Failed to checkout local branch in {repo_path}: {str(e)}"
                    )
                    return False
        else:
            # Create a new branch from current HEAD
            try:
                run_git(
                    ["checkout", "-b", branch_name],
                    "create and checkout new branch",
                    repo_path,
                )
            except Exception as e:
                print(f"\n❌ Failed to create new branch in {repo_path}: {str(e)}")
                try:
                    # Fallback: try to create branch first, then switch
                    run_git(["branch", branch_name], "create branch", repo_path)
                    run_git(["checkout", branch_name], "switch to branch", repo_path)
                except Exception as e:
                    print(
                        f"\n❌ Fallback branch creation also failed in {repo_path}: {str(e)}"
                    )
                    return False
            print(f"Created branch '{branch_name}' in {repo_path}")

        print(f"✅ Switched to branch '{branch_name}' in {repo_path}")
        return True

    except Exception as e:
        print(f"\n❌ Error in {repo_path}: {str(e)}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create and switch to a branch in all repositories"
    )
    parser.add_argument(
        "branch_name", help="Name of the branch to create and switch to"
    )
    args = parser.parse_args()

    if not args.branch_name:
        print("\n❌ Branch name is required")
        sys.exit(1)

    git_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    # First create/switch branch in root repo
    print("\n🔄 Processing root repository...")
    if not create_and_switch_branch(git_root, args.branch_name):
        sys.exit(1)

    # Load repo names
    repos = load_repos(names_only=True)

    if not repos:
        print("\n❌ No repositories found in repos.json")
        sys.exit(1)

    print("\n🔄 Processing sub-repositories...")
    success = True

    for repo_name in repos:
        repo_path = os.path.join(git_root, repo_name)
        if not create_and_switch_branch(repo_path, args.branch_name):
            success = False

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
