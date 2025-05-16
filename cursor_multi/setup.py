#!/usr/bin/env python3

import os

from .rules import (
    cleanup_old_imported_rules,
    import_cursor_rules,
    track_imported_rules,
)
from .utils import get_app_packages, get_git_root, load_repos, run_git


def get_current_branch(repo_path: str) -> str:
    """Get the current branch name of a git repository."""
    try:
        result = run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            "determine current branch",
            repo_path,
        )
        return result.stdout.strip()
    except SystemExit:
        print("⚠️  Warning: Could not determine current branch, using 'main'")
        return "main"


def clone_repos():
    """Clone all repositories from the repos.json file."""
    repos = load_repos()
    root_dir = get_git_root()
    repo_names = []

    # Get the current branch of the parent repo
    current_branch = get_current_branch(root_dir)
    print(f"📌 Current branch: {current_branch}")

    for repo_url in repos:
        repo_name = repo_url.split("/")[-1]
        repo_names.append(repo_name)
        repo_path = os.path.join(root_dir, repo_name)

        if os.path.exists(repo_path):
            print(f"📁 {repo_name} already exists, skipping...")
            continue

        print(f"\n🔄 Cloning {repo_name}...")

        # First clone the default branch
        run_git(
            ["clone", repo_url, repo_path],
            f"clone {repo_name}",
        )

        # Then checkout the same branch as parent repo if it exists
        try:
            run_git(
                ["checkout", current_branch],
                f"checkout branch {current_branch}",
                repo_path,
            )
            print(
                f"✅ Successfully cloned {repo_name} and checked out branch {current_branch}"
            )
        except SystemExit:
            print(
                f"⚠️  Branch {current_branch} not found in {repo_name}, staying on default branch"
            )

    return repo_names


def update_ignore_files(repo_names: list[str], imported_rules: list[str] | None = None):
    """Update .gitignore and .ignore with repository names and imported rules."""
    git_root = get_git_root()
    gitignore_path = os.path.join(git_root, ".gitignore")
    ignore_path = os.path.join(git_root, ".ignore")

    # Handle .gitignore
    existing_gitignore = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_gitignore = [line.strip() for line in f.readlines()]

    gitignore_to_add = []

    # Add imported rules to gitignore
    if imported_rules:
        for rule in imported_rules:
            rule_entry = f".cursor/rules/{rule}"
            if rule_entry not in existing_gitignore:
                gitignore_to_add.append(rule_entry)

    # Add repos to gitignore
    for repo in repo_names:
        repo_entry = f"{repo}/"
        if repo_entry not in existing_gitignore:
            gitignore_to_add.append(repo_entry)

    if gitignore_to_add:
        with open(gitignore_path, "a") as f:
            if existing_gitignore and not existing_gitignore[-1] == "":
                f.write("\n")
            if any(rule.startswith(".cursor/rules/") for rule in gitignore_to_add):
                f.write("# Ignore imported cursor rules\n")
            f.write("\n".join(gitignore_to_add) + "\n")
        print("✅ Updated .gitignore with new entries")

    # Handle .ignore
    existing_ignore = []
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            existing_ignore = [line.strip() for line in f.readlines()]

    ignore_to_add = []
    for repo in repo_names:
        repo_entry = f"!{repo}/"
        if repo_entry not in existing_ignore:
            ignore_to_add.append(repo_entry)

    if ignore_to_add:
        with open(ignore_path, "a") as f:
            if not existing_ignore:
                f.write("# Allow us to search inside these gitignored directories.\n")
            elif not existing_ignore[-1] == "":
                f.write("\n")
            f.write("\n".join(ignore_to_add) + "\n")
        print("✅ Updated .ignore with new repositories")


def generate_app_requirements(repo_names: list[str]):
    """Generate app_requirements.txt based on web.app_packages entry points in pyproject.toml."""
    git_root = get_git_root()
    app_packages = get_app_packages(repo_names)

    # If we found any app packages, generate or update app_requirements.txt
    if app_packages:
        app_requirements_path = os.path.join(git_root, "web", "app_requirements.txt")
        requirements_content = "\n".join(f"-e ../{package}" for package in app_packages)

        # Only write if file doesn't exist or content would be different
        if not os.path.exists(app_requirements_path):
            with open(app_requirements_path, "w") as f:
                f.write(requirements_content + "\n")
            print("✅ Created app_requirements.txt with web app packages")
        else:
            with open(app_requirements_path, "r") as f:
                existing_content = f.read().strip()
            if existing_content != requirements_content:
                with open(app_requirements_path, "w") as f:
                    f.write(requirements_content + "\n")
                print("✅ Updated app_requirements.txt with web app packages")


def main():
    print("🚀 Setting up development environment...")

    # Clone repositories and get their names
    repo_names = clone_repos()

    # Generate app_requirements.txt based on web.app_packages entry points
    generate_app_requirements(repo_names)

    # Clean up any previously imported rules
    print("\n🔄 Cleaning up old imported rules...")
    git_root = get_git_root()
    cleanup_old_imported_rules(git_root)

    # Import cursor rules from each repository
    print("\n🔄 Importing Cursor rules...")
    imported_rules = import_cursor_rules(git_root, repo_names)

    # Track the imported rules
    track_imported_rules(git_root, imported_rules)

    # Update .gitignore and .ignore with repo names and imported rules
    update_ignore_files(repo_names, imported_rules)

    print("\n✨ All setup tasks completed successfully!")


if __name__ == "__main__":
    main()
