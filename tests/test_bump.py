import pathlib
from unittest.mock import patch

import pytest

from src.releaser import bump
from src.releaser.core.repository import GitRepository

from .helper import CZ_JSON, Origin


def test_no_version_bump(tmp_path: pathlib.Path) -> None:
    origin = Origin(tmp_path)
    origin.commit(".cz.json", CZ_JSON, "docs: v0.0.0")

    path = origin.clone().working_tree_dir
    repo = GitRepository(path)
    next_version, changelog = bump.bump(repo, "main", None)

    assert next_version is None
    assert changelog is None


@patch("src.releaser.core.commits.commitizen")
def test_unexpected_exception(mock_commitizen, tmp_path: pathlib.Path) -> None:
    mock_commitizen.side_effect = Exception("Unexpected exception")
    path = Origin(tmp_path).clone().working_tree_dir
    repo = GitRepository(path)
    with pytest.raises(Exception, match="Unexpected exception"):
        bump.bump(repo, "main", None)
