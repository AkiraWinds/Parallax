"""Diff-scope resolution tests (Section 27.1's report-adjacent coverage;
also exercises the fallback order shared with `.claude/skills/sanyi`'s
own "Mode: review" input rule).

Builds a throwaway git repo per test rather than mocking subprocess, so
these tests exercise the actual git plumbing the orchestrator relies on.
"""

from __future__ import annotations

import subprocess

import pytest

from parallax.orchestration.diff_scope import (
    DiffScopeMode,
    NoBaseBranchError,
    resolve_diff_scope,
)


def _git(repo: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path) -> str:
    repo_path = str(tmp_path)
    _git(repo_path, "init", "-q", "-b", "main")
    _git(repo_path, "config", "user.email", "test@example.com")
    _git(repo_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("hello\n")
    _git(repo_path, "add", "README.md")
    _git(repo_path, "commit", "-q", "-m", "init")
    return repo_path


def test_staged_takes_priority(repo, tmp_path):
    (tmp_path / "staged.py").write_text("x = 1\n")
    (tmp_path / "unstaged.py").write_text("y = 2\n")
    _git(repo, "add", "staged.py")

    scope = resolve_diff_scope(repo)
    assert scope.mode == DiffScopeMode.STAGED
    assert scope.changed_files == ["staged.py"]


def test_working_tree_used_when_nothing_staged(repo, tmp_path):
    (tmp_path / "README.md").write_text("hello, edited\n")

    scope = resolve_diff_scope(repo)
    assert scope.mode == DiffScopeMode.WORKING_TREE
    assert scope.changed_files == ["README.md"]


def test_branch_diff_used_when_clean(repo, tmp_path):
    _git(repo, "checkout", "-q", "-b", "feature")
    (tmp_path / "feature.py").write_text("z = 3\n")
    _git(repo, "add", "feature.py")
    _git(repo, "commit", "-q", "-m", "add feature")

    scope = resolve_diff_scope(repo, base_branch="main")
    assert scope.mode == DiffScopeMode.BRANCH_DIFF
    assert scope.base_ref == "main"
    assert scope.changed_files == ["feature.py"]


def test_raises_when_clean_and_no_base_branch_given(repo):
    with pytest.raises(NoBaseBranchError):
        resolve_diff_scope(repo)
