#!/usr/bin/env python3
"""
Small, opinionated git helper for DustCollectorSoftware.

Design goals:
- Safe-by-default.
- No history rewriting, no force pushes.
- Focus on one branch (TARGET_BRANCH).
- Preview before staging everything.
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

TARGET_BRANCH = "v2-architecture"

# If True, gitmenu refuses to stage if it sees suspicious junk files.
# You can set this False if it ever gets in your way.
REFUSE_SUSPICIOUS_STAGE = True

SUSPICIOUS_PATTERNS = (
    ".~lock.",
    "/.direnv/",
    "/__pycache__/",
)


def run_git(args: List[str], capture: bool = True) -> str:
    """Run a git command. Raise on failure. Optionally capture stdout."""
    cmd = ["git"] + args
    try:
        if capture:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            return out
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


def print_cmd_block(title: str, cmd: List[str]) -> None:
    print(f"\n--- {title} ---")
    print(f"$ {' '.join(['git'] + cmd)}")
    print(run_git(cmd).rstrip())


def list_porcelain() -> str:
    """Return `git status --porcelain` output."""
    return run_git(["status", "--porcelain"]).rstrip()


def list_untracked() -> str:
    """Return untracked files (excluding ignored)."""
    return run_git(["ls-files", "--others", "--exclude-standard"]).rstrip()


def list_staged_files() -> str:
    """Return staged file list."""
    return run_git(["diff", "--name-only", "--cached"]).rstrip()


def show_status() -> None:
    """Show where we are and current status."""
    top = ensure_in_repo()
    branch = get_current_branch()

    print("\n=== Repository status ===")
    print(f"Repo root: {top}")
    print(f"Current branch: {branch}")

    print_cmd_block("git status -sb", ["status", "-sb"])

    print(f"\n--- Last 8 commits on {TARGET_BRANCH} ---")
    try:
        log_out = run_git(["log", "-8", "--oneline", "--decorate", TARGET_BRANCH])
        print(log_out.rstrip())
    except Exception:
        print(f"(No log found for branch {TARGET_BRANCH}?)")

    print("========================\n")


def show_diff_unstaged() -> None:
    ensure_in_repo()
    print_cmd_block("git diff (unstaged)", ["diff"])


def show_diff_staged() -> None:
    ensure_in_repo()
    print_cmd_block("git diff --cached (staged)", ["diff", "--cached"])


def ensure_on_target_branch() -> bool:
    current = get_current_branch()
    if current != TARGET_BRANCH:
        print(
            f"\nRefusing: current branch is '{current}', not '{TARGET_BRANCH}'.\n"
            f"Checkout {TARGET_BRANCH} first.\n"
        )
        return False
    return True


def sync_from_origin() -> None:
    """Get latest tip of TARGET_BRANCH safely."""
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

    current = get_current_branch()
    if current != TARGET_BRANCH:
        print(f"\n[2] git checkout {TARGET_BRANCH}")
        try:
            run_git(["checkout", TARGET_BRANCH], capture=False)
        except Exception:
            print(f"\nCould not checkout {TARGET_BRANCH}. Does it exist locally?\n")
            return

    print(f"\n[3] git pull --ff-only origin {TARGET_BRANCH}")
    try:
        run_git(["pull", "--ff-only", "origin", TARGET_BRANCH], capture=False)
    except Exception:
        print(
            "\nPull failed (local and remote likely diverged).\n"
            "Stop and resolve manually (or ask Bob).\n"
        )
        return

    print("\n== Sync complete ==\n")


def _refuse_if_suspicious(files_text: str) -> bool:
    if not REFUSE_SUSPICIOUS_STAGE:
        return False
    lower = files_text.lower()
    hits = [p for p in SUSPICIOUS_PATTERNS if p.lower() in lower]
    if hits:
        print("\nRefusing to stage because suspicious junk appears in changes:")
        for h in hits:
            print(f"  - matched: {h}")
        print("\nFix: add/confirm .gitignore rules, then re-run.\n")
        return True
    return False


def add_and_commit() -> None:
    """Add files and commit with a message (with preview)."""
    ensure_in_repo()

    print("\n=== Pre-commit review ===")
    print_cmd_block("git status -sb", ["status", "-sb"])

    porcelain = list_porcelain()
    if porcelain.strip() == "":
        print("\nNothing to commit.\n")
        return

    untracked = list_untracked()
    print("\n--- Changes (porcelain) ---")
    print(porcelain if porcelain else "(none)")
    print("\n--- Untracked files ---")
    print(untracked if untracked else "(none)")

    # Optional safety: refuse staging if obvious junk appears.
    combined = porcelain + "\n" + untracked
    if _refuse_if_suspicious(combined):
        return

    ans = input(
        "\nStage ALL modified + untracked files with 'git add -A'? [y/N]: "
    ).strip().lower()
    if ans != "y":
        print("\nAborted staging.\n")
        return

    print("\n[1] git add -A")
    try:
        run_git(["add", "-A"], capture=False)
    except Exception:
        print("\nStaging failed.\n")
        return

    print("\n--- Status AFTER staging ---")
    print(run_git(["status", "-sb"]).rstrip())

    staged = list_staged_files()
    print("\n--- Staged files ---")
    print(staged if staged else "(none?)")

    # Final confirmation before commit
    ans2 = input("\nProceed to commit? [y/N]: ").strip().lower()
    if ans2 != "y":
        print("\nCommit aborted. (Staging remains; use 'git restore --staged .' if needed.)\n")
        return

    msg = input("\nCommit message (leave empty to abort): ").strip()
    if not msg:
        print("\nCommit aborted (empty message).\n")
        return

    print(f'\n[2] git commit -m "{msg}"')
    try:
        run_git(["commit", "-m", msg], capture=False)
    except Exception:
        print("\nCommit failed.\n")
        return

    print("\n== Commit complete ==\n")


def push_branch() -> None:
    """Push current branch to origin/TARGET_BRANCH."""
    ensure_in_repo()
    if not ensure_on_target_branch():
        return

    print(f"\n== Pushing '{TARGET_BRANCH}' to origin ==")
    print(f"[1] git push origin {TARGET_BRANCH}")
    try:
        run_git(["push", "origin", TARGET_BRANCH], capture=False)
    except Exception:
        print("\nPush failed.\n")
        return

    print("\n== Push complete ==\n")


def create_branch_from_target() -> None:
    """Create a new branch from TARGET_BRANCH (optional helper)."""
    ensure_in_repo()

    name = input("\nNew branch name (leave empty to abort): ").strip()
    if not name:
        print("\nAborted.\n")
        return

    # Ensure we're up to date first
    if not working_tree_clean():
        print("\nRefusing: working tree not clean.\n")
        return

    print("\n[1] git fetch origin")
    run_git(["fetch", "origin"], capture=False)

    print(f"\n[2] git checkout {TARGET_BRANCH}")
    run_git(["checkout", TARGET_BRANCH], capture=False)

    print(f"\n[3] git pull --ff-only origin {TARGET_BRANCH}")
    run_git(["pull", "--ff-only", "origin", TARGET_BRANCH], capture=False)

    print(f"\n[4] git checkout -b {name}")
    run_git(["checkout", "-b", name], capture=False)

    print(f"\nCreated branch '{name}' from '{TARGET_BRANCH}'.\n")


def menu() -> None:
    ensure_in_repo()

    while True:
        print(
            "Git menu (v2-architecture helper)\n"
            "  1) Get latest tip from origin/v2-architecture (safe ff-only)\n"
            "  2) Add files and commit (with preview + confirmations)\n"
            "  3) Push v2-architecture to origin\n"
            "  4) Verify where I am (status)\n"
            "  5) Show diff (unstaged)\n"
            "  6) Show diff (staged)\n"
            "  7) Create new branch from v2-architecture\n"
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
        elif choice == "5":
            show_diff_unstaged()
        elif choice == "6":
            show_diff_staged()
        elif choice == "7":
            create_branch_from_target()
        elif choice == "0":
            print("Bye.\n")
            break
        else:
            print("Unknown choice. Try again.\n")


def main(argv: Optional[List[str]] = None) -> None:
    _ = argv
    menu()


if __name__ == "__main__":
    main()
