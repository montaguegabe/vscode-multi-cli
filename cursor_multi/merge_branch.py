#!/usr/bin/env python3

import argparse
import os
import sys

from cursor_multi.utils import (
    check_branch_existence,
    load_repos,
    run_git,
    validate_git_repo,
)


def merge_branch(repo_path: str, source_branch: str, target_branch: str) -> bool:
    """Merge source_branch into target_branch in the specified repository."""
    try:
        if not validate_git_repo(repo_path):
            return False

        # Check if both branches exist
        for branch in [source_branch, target_branch]:
            exists_locally, exists_remotely = check_branch_existence(repo_path, branch)
            if not exists_locally and not exists_remotely:
                print(
                    f"\n❌ Branch '{branch}' does not exist locally or remotely in {repo_path}"
                )
                return False

        # Switch to target branch
        try:
            run_git(["checkout", target_branch], "checkout target branch", repo_path)
        except Exception as e:
            print(f"\n❌ Failed to checkout target branch in {repo_path}: {str(e)}")
            return False

        # Perform the merge
        try:
            print(
                f"\n🔄 Merging '{source_branch}' into '{target_branch}' in {repo_path}"
            )
            run_git(["merge", source_branch], "merge branches", repo_path)
            print(
                f"✅ Successfully merged '{source_branch}' into '{target_branch}' in {repo_path}"
            )
            return True
        except Exception as e:
            print(f"\n❌ Merge failed in {repo_path}: {str(e)}")
            print("Please resolve conflicts manually and commit the changes.")
            return False

    except Exception as e:
        print(f"\n❌ Error in {repo_path}: {str(e)}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge source branch into target branch across all repositories"
    )
    parser.add_argument("source_branch", help="Name of the source branch to merge from")
    parser.add_argument("target_branch", help="Name of the target branch to merge into")
    args = parser.parse_args()

    if not args.source_branch or not args.target_branch:
        print("\n❌ Both source and target branch names are required")
        sys.exit(1)

    git_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    # First merge in root repo
    print("\n🔄 Processing root repository...")
    if not merge_branch(git_root, args.source_branch, args.target_branch):
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
        if not merge_branch(repo_path, args.source_branch, args.target_branch):
            success = False

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
