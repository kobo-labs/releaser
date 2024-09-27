import argparse

import pytest
from commitizen.exceptions import InvalidCommitMessageError

from src.releaser import check, cli
from src.releaser.core.repository import GitRepository

from .helper import Origin


def test_check_success(tmp_path) -> None:
    origin = Origin(tmp_path, additional_branches=["feat/branch"])
    origin.commit(
        "README.md", "feature commit in feature branch", "feat: branch", "feat/branch"
    )

    path = origin.clone(["main", "feat/branch"]).working_tree_dir

    args = argparse.Namespace
    args.repository = path
    args.action = "check"
    args.check_from = "main"

    cli.main(args)


def test_check_incorrect_commit_message(tmp_path) -> None:
    origin = Origin(tmp_path, additional_branches=["feat/branch"])
    origin.commit(
        "README.md",
        "feature commit in feature branch",
        "false-type: branch",
        "feat/branch",
    )

    path = origin.clone(["feat/branch"]).working_tree_dir
    repo = GitRepository(path)

    with pytest.raises(InvalidCommitMessageError):
        check.check(repo, "main")


def test_check_from_nonexisting(tmp_path) -> None:
    origin = Origin(tmp_path)
    path = origin.clone().working_tree_dir
    repo = GitRepository(path)

    with pytest.raises(ValueError, match="Could not find branch 'non-existing'."):
        check.check(repo, "non-existing")
