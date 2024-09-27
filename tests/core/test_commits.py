from unittest.mock import patch

import pytest

from src.releaser.core import commits
from src.releaser.core.version import Version
from tests.helper import COMMIT_URL


@patch("src.releaser.core.commits.commitizen")
def test_bump_no_exception_raised(mock_commitizen, tmp_path) -> None:
    with pytest.raises(RuntimeError):
        commits.bump(tmp_path)


def test_extract_version_malformed() -> None:
    with pytest.raises(RuntimeError):
        commits.extract_version("")


def test_get_current_version(tmp_path) -> None:
    with pytest.raises(RuntimeError):
        commits.get_current_version(tmp_path)


@patch("src.releaser.core.commits.commitizen")
@patch("src.releaser.core.commits.get_current_version")
def test_get_changelog_exception_raised(
    mock_get_current_version, mock_commitizen, tmp_path
) -> None:
    mock_commitizen.side_effect = Exception("Test exception")
    with pytest.raises(Exception, match="Test exception"):
        commits.get_changelog(tmp_path, COMMIT_URL, Version("0.1.0"), None)


@patch("src.releaser.core.commits.commitizen")
@patch("src.releaser.core.commits.get_current_version")
def test_get_changelog_no_exception_raised(
    mock_get_current_version, mock_commitizen, tmp_path
) -> None:
    with pytest.raises(RuntimeError):
        commits.get_changelog(tmp_path, COMMIT_URL, Version("0.1.0"), None)
