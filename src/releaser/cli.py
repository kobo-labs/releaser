"""Module for interacting with the release package from the CLI."""

import argparse
import os
import pathlib
import uuid

from . import bump, check, release
from .changelog_templates import templates
from .core.repository import GitRepository
from .core.version import Version

GITHUB_OUTPUT = "GITHUB_OUTPUT"
RUNNER_TEMP = "RUNNER_TEMP"


def parse(args: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="python -m releaser",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    action = parser.add_subparsers(
        dest="action", help="Available actions.", required=True
    )

    release = action.add_parser(
        "release", help="Release a new version of the repository."
    )
    release.add_argument(
        "-s",
        "--source",
        type=str,
        default="main",
        help="Source branch containing commits to release.",
    )
    release.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without pushing changes.",
    )
    release.add_argument(
        "-t",
        "--changelog-template",
        type=str,
        choices=templates.get_all_templates(),
        help="Specify the changelog template to use. If not specified, default "
        "template will be used.",
    )

    check = action.add_parser("check", help="Check commit message format.")
    check.add_argument(
        "-f",
        "--check-from",
        type=str,
        default="main",
        help="Check commit message format from given branch to HEAD.",
    )

    parser.add_argument(
        "repository",
        type=pathlib.Path,
        help="Directory of the release repository.",
    )

    return parser.parse_args(args)


def get_env_variable(variable_name: str) -> str:
    """Return value of the environment variable with the given name."""
    value = os.getenv(variable_name)
    if value is None:
        msg = f"The environment variable '{variable_name}' is not set."
        raise KeyError(msg)
    return value


def write_changelog(runner_temp: pathlib.Path, changelog: str) -> pathlib.Path:
    """Write version changelog into temporary file."""
    temp_changelog_file = runner_temp / f"{uuid.uuid4()!s}.md"
    with temp_changelog_file.open(mode="w") as f:
        f.write(changelog)
    return temp_changelog_file


def output_release_ready(
    github_output: pathlib.Path,
    release_ready: bool,
) -> None:
    """Write release ready status into github output."""
    with github_output.open(mode="a") as f:
        release_ready_value = "true" if release_ready else "false"
        f.write(f"ready={release_ready_value}\n")


def output_release(
    github_output: pathlib.Path,
    next_version: Version,
    temp_changelog_file: pathlib.Path,
) -> None:
    """Write release info into github output."""
    with github_output.open(mode="a") as f:
        f.write(f"tag={next_version.get_release_tag()}\n")
        f.write(f"changelog={temp_changelog_file}\n")


def main(args: argparse.Namespace) -> None:
    """Run release logic."""
    repo = GitRepository(args.repository)
    if args.action == "check":
        check.check(repo, args.check_from)
    elif args.action == "release":
        github_output = pathlib.Path(get_env_variable(GITHUB_OUTPUT))
        runner_temp = pathlib.Path(get_env_variable(RUNNER_TEMP))
        next_version, changelog = bump.bump(repo, args.source, args.changelog_template)
        release_ready = bool(next_version and changelog)
        output_release_ready(github_output, release_ready)
        if next_version and changelog:
            release.release(
                repo, args.source, next_version, changelog, dry_run=args.dry_run
            )
            temp_changelog_file = write_changelog(runner_temp, changelog)
            output_release(github_output, next_version, temp_changelog_file)
