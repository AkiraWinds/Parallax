"""Diff scope resolution shared by Stage 1 (parent spec Section 10) and
SANYI's own review mode (`.claude/skills/sanyi/SKILL.md` "Mode: review").

Both describe the same fallback order for "what is the current diff":
staged changes if any; else uncommitted working-tree changes if any; else
current branch vs. the default branch. This module makes that one rule a
single, tested implementation instead of two independent descriptions that
could drift apart.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum


class DiffScopeMode(str, Enum):
    STAGED = "staged"
    WORKING_TREE = "working_tree"
    BRANCH_DIFF = "branch_diff"


@dataclass
class DiffScope:
    mode: DiffScopeMode
    changed_files: list[str]
    base_ref: str | None = None


class NoBaseBranchError(RuntimeError):
    """Raised when falling back to branch_diff but no base branch was
    given and none could be inferred — the caller should ask the human
    which range to review (SANYI SKILL.md "Mode: review", parent spec
    Stage 0)."""


class GitCommandError(RuntimeError):
    """A `git` subprocess call failed. Carries git's own stderr — a bare
    `CalledProcessError` only carries the exit code, which leaves the
    caller (a human reading a CLI error, or an agent parsing it) with no
    way to tell a real repo problem from something as simple as a `diff`
    alias in the target repo's `.gitconfig` adding a conflicting flag."""


def _run_git(args: list[str], cwd: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitCommandError(
            f"`git {' '.join(args)}` failed in {cwd!r} "
            f"(exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def _changed_files(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.strip()]


def resolve_diff_scope(
    repo_path: str = ".",
    base_branch: str | None = None,
) -> DiffScope:
    """Resolve the current diff scope using the shared fallback order.

    Raises NoBaseBranchError if every earlier tier is empty and no
    `base_branch` was supplied — matching the SANYI skill's instruction to
    ask which range to review rather than guessing.
    """
    staged = _changed_files(_run_git(["diff", "--cached", "--name-only"], repo_path))
    if staged:
        return DiffScope(mode=DiffScopeMode.STAGED, changed_files=staged)

    working_tree = _changed_files(_run_git(["diff", "--name-only"], repo_path))
    if working_tree:
        return DiffScope(mode=DiffScopeMode.WORKING_TREE, changed_files=working_tree)

    if not base_branch:
        raise NoBaseBranchError(
            "no staged or uncommitted changes, and no base branch given — "
            "ask the human which range to review"
        )

    branch_diff = _changed_files(
        _run_git(["diff", f"{base_branch}...HEAD", "--name-only"], repo_path)
    )
    return DiffScope(
        mode=DiffScopeMode.BRANCH_DIFF, changed_files=branch_diff, base_ref=base_branch
    )
