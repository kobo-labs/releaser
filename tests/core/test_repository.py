import pathlib

import pytest

from src.releaser.core.repository import GitRepository
from tests.helper import Origin


def test_master_branch(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path, default_branch="master").clone().working_tree_dir
    repo = GitRepository(path)
    assert repo.repo.head.reference.name == "master"


def test_broken_default_branch(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path, default_branch="something-else").clone().working_tree_dir
    with pytest.raises(ValueError, match="Default branch not found."):
        GitRepository(path)


def test_checkout_head(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path).clone().working_tree_dir
    repo = GitRepository(path)
    repo.checkout("HEAD")
    assert repo.repo.head.reference.name == "main"


def test_merge_source_branch_doesnt_exist(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path).clone().working_tree_dir
    repo = GitRepository(path)
    with pytest.raises(RuntimeError, match="Could not find source branch head."):
        repo.merge("doesnt_exist", "v0", "Merge main into v0")


def test_merge_target_branch_doesnt_exist(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path).clone().working_tree_dir
    repo = GitRepository(path)
    with pytest.raises(RuntimeError, match="Could not find target branch head."):
        repo.merge("main", "v0", "Merge main into v0")


def test_clean_repository_after_merge(tmp_path: pathlib.Path) -> None:
    # * chore: delete file (origin/chore/delete-file)
    # | * docs: something (HEAD -> main, origin/main)
    # |/
    # * chore: add file
    # * first commit
    origin = Origin(tmp_path)
    origin.commit("file_to_be_deleted.txt", "to be deleted", "chore: add file")
    origin.create_branch("chore/delete-file")
    origin.commit("README.md", "another unrelated commit in main", "docs: something")
    origin.delete("file_to_be_deleted.txt", "chore: delete file", "chore/delete-file")

    path = origin.clone().working_tree_dir
    repo = GitRepository(path)

    repo.merge("chore/delete-file", "main")

    assert repo.repo.untracked_files == []
    assert [diff.a_path for diff in repo.repo.index.diff(None)] == []


def test_get_url(tmp_path: pathlib.Path) -> None:
    path = Origin(tmp_path).clone().working_tree_dir
    repo = GitRepository(path)
    assert repo.get_url() != ""
