#!/usr/bin/env python3
"""
Small, opinionated git helper for DustCollectorSoftware.

Intended usage:
    - Run from anywhere inside the repo:
        python gitmenu.py
    - Only works with the 'v2-architecture' branch.
    - No history rewriting, no force pushes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional

TARGET_BRANCH = "v2-architecture"


def run_git(args: List[str], capture: bool = True) -> str:
    """Run a git command. Raise on failure. Optionally capture stdout."""
    cmd = ["git"] + args
    try:
        if capture:
            out = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, text=True
            )
            return out
        else:
            subprocess.check_call(cmd)
            return ""
    except subprocess.CalledProcessError as exc:
        print("\n[git error]")
        print(f"$ {' '.join(cmd)}")
        print(exc.output)
        raise


def ensure_in_repo() -> str:
    """Ensure we are inside a git repo and return its top-level directory."""
    try:
        top = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.STDOUT,
                text=True,
            )
            .strip()
        )
    except subprocess.CalledProcessError as exc:
        print("Error: this does not appear to be inside a git repository.")
        print(exc.output)
        sys.exit(1)
    return top


def get_current_branch() -> str:
    """Return the current branch name."""
    out = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip()


def working_tree_clean() -> bool:
    """True if there are no staged or unstaged changes."""
    out = run_git(["status", "--porcelain"])
    return out.strip() == ""


def show_status() -> None:
    """Option 4: show where we are and current status."""
    top = ensure_in_repo()
    branch = get_current_branch()

    print("\n=== Repository status ===")
    print(f"Repo root: {top}")
    print(f"Current branch: {branch}")

    print("\n--- git status -sb ---")
    print(run_git(["status", "-sb"]).rstrip())

    print(f"\n--- Last 5 commits on {TARGET_BRANCH} ---")
    try:
        log_out = run_git(
            ["log", "-5", "--oneline", "--decorate", TARGET_BRANCH]
        )
        print(log_out.rstrip())
    except Exception:
        print(f"(No log found for branch {TARGET_BRANCH}?)")

    print("========================\n")


def sync_from_origin() -> None:
    """Option 1: get latest tip of TARGET_BRANCH safely."""
    ensure_in_repo()

    if not working_tree_clean():
        print(
            "\nRefusing to sync: working tree is NOT clean.\n"
            "Commit, stash, or discard changes first.\n"
        )
        return

    print(f"\n== Syncing branch '{TARGET_BRANCH}' from origin ==")

    print("\n[1] git fetch origin")
    run_git(["fetch", "origin"], capture=False)

    # Switch to target branch if needed
    current = get_current_branch()
    if current != TARGET_BRANCH:
        print(f"\n[2] git checkout {TARGET_BRANCH}")
        try:
            run_git(["checkout", TARGET_BRANCH], capture=False)
        except Exception:
            print(
                f"\nCould not checkout {TARGET_BRANCH}. "
                "Does it exist locally?"
            )
            return

    print(f"\n[3] git pull --ff-only origin {TARGET_BRANCH}")
    try:
        run_git(["pull", "--ff-only", "origin", TARGET_BRANCH], capture=False)
    except Exception:
        print(
            "\nPull failed (probably because local and remote diverged).\n"
            "You may need to do a manual merge/rebase, or ask Bob for help."
        )
        return

    print("\n== Sync complete ==\n")


def add_and_commit() -> None:
    """Option 2: add files and commit with a message."""
    ensure_in_repo()

    print("\nCurrent short status before staging:\n")
    print(run_git(["status", "-sb"]).rstrip())

    ans = input(
        "\nStage ALL modified and untracked files with 'git add -A'? [y/N]: "
    ).strip().lower()
    if ans == "y":
        print("\n[1] git add -A")
        try:
            run_git(["add", "-A"], capture=False)
        except Exception:
            print("\nStaging failed.")
            return
    else:
        print(
            "\nNo files staged automatically. "
            "You can stage manually in another shell if you want."
        )

    print("\nStatus AFTER staging:\n")
    print(run_git(["status", "-sb"]).rstrip())

    msg = input("\nCommit message (leave empty to abort): ").strip()
    if not msg:
        print("\nCommit aborted (empty message).\n")
        return

    print(f"\n[2] git commit -m \"{msg}\"")
    try:
        run_git(["commit", "-m", msg], capture=False)
    except Exception:
        print("\nCommit failed.")
        return

    print("\n== Commit complete ==\n")


def push_branch() -> None:
    """Option 3: push current branch to origin/TARGET_BRANCH."""
    ensure_in_repo()
    current = get_current_branch()

    if current != TARGET_BRANCH:
        print(
            f"\nRefusing to push: current branch is '{current}', "
            f"not '{TARGET_BRANCH}'."
        )
        print(
            f"Checkout {TARGET_BRANCH} first if you really intend to push it."
        )
        return

    print(f"\n== Pushing '{TARGET_BRANCH}' to origin ==")
    print(f"[1] git push origin {TARGET_BRANCH}")
    try:
        run_git(["push", "origin", TARGET_BRANCH], capture=False)
    except Exception:
        print("\nPush failed.")
        return

    print("\n== Push complete ==\n")


def menu() -> None:
    ensure_in_repo()

    while True:
        print(
            "Git menu (v2-architecture helper)\n"
            "  1) Get latest tip from origin/v2-architecture\n"
            "  2) Add files and commit (with message)\n"
            "  3) Push v2-architecture to origin\n"
            "  4) Verify where I am (status)\n"
            "  0) Quit\n"
        )
        choice = input("Select option: ").strip()

        if choice == "1":
            sync_from_origin()
        elif choice == "2":
            add_and_commit()
        elif choice == "3":
            push_branch()
        elif choice == "4":
            show_status()
        elif choice == "0":
            print("Bye.\n")
            break
        else:
            print("Unknown choice. Try again.\n")


def main(argv: Optional[List[str]] = None) -> None:
    # For now we ignore argv and just present the menu.
    menu()


if __name__ == "__main__":
    main()
