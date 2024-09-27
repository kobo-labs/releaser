import pathlib

import pytest

from src.releaser import cli


def test_parse_release() -> None:
    args = cli.parse(
        [
            "release",
            "repo/path",
        ]
    )
    assert args.repository == pathlib.Path("repo/path")
    assert args.source == "main"
    assert args.dry_run is False
    assert args.action == "release"
    assert args.changelog_template is None


def test_parse_changelog_template() -> None:
    args = cli.parse(
        [
            "release",
            "-t",
            "github_linked_sha.md.j2",
            "repo/path",
        ]
    )
    assert args.repository == pathlib.Path("repo/path")
    assert args.source == "main"
    assert args.dry_run is False
    assert args.action == "release"
    assert args.changelog_template == "github_linked_sha.md.j2"


def test_parse_check() -> None:
    args = cli.parse(["check", "-f", "master", "repo/path"])
    assert args.repository == pathlib.Path("repo/path")
    assert args.action == "check"
    assert args.check_from == "master"


def test_missing_environment_variable() -> None:
    with pytest.raises(
        KeyError, match="The environment variable 'missing' is not set."
    ):
        cli.get_env_variable("missing")
