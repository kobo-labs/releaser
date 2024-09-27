"""Module for interacting with commit history."""

import io
import os
import pathlib
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout

from commitizen.cli import main as commitizen
from commitizen.exceptions import DryRunExit

from releaser.changelog_templates import templates

from .version import Version


@contextmanager
def set_working_dir(new_dir: pathlib.Path) -> Iterator[None]:
    """Change working directory."""
    original_dir = pathlib.Path.cwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(original_dir)


@contextmanager
def set_system_args(args: list[str]) -> Iterator[None]:
    """Set system arguments."""
    original_argv = sys.argv
    try:
        sys.argv = args
        yield
    finally:
        sys.argv = original_argv


@contextmanager
def set_changelog_template(
    path: pathlib.Path, url: str, args: list[str], changelog_template: str | None
) -> Iterator[None]:
    """Create a symbolic link to the template file and remove it afterwards."""
    if changelog_template and __package__:
        commit_url = f"{url.removesuffix(".git")}/commit/"
        template_file = templates.get_template_file(changelog_template)
        destination_template_symlink = path / changelog_template
        relative_template_path = destination_template_symlink.relative_to(path)
        try:
            os.symlink(template_file, destination_template_symlink)
            args.extend(
                [
                    "--template",
                    str(relative_template_path),
                    "--extra",
                    f"commit_url={commit_url}",
                ]
            )
            yield
        finally:
            destination_template_symlink.unlink()
    else:
        yield


def bump(path: pathlib.Path) -> Version:
    """Check if repository version can be bumped."""
    stdout = io.StringIO()
    try:
        with (
            redirect_stdout(stdout),
            set_working_dir(path),
            set_system_args(["cz", "bump", "--yes", "--dry-run"]),
        ):
            commitizen()
    except DryRunExit:
        return extract_version(stdout.getvalue())
    except Exception:
        raise
    else:
        msg = f"Expected {DryRunExit} exception was not raised."
        raise RuntimeError(msg)


def extract_version(log: str) -> Version:
    """Extract semantic version from commitizen message."""
    pattern = r"tag to create: v(\d+\.\d+\.\d+)"
    match = re.search(pattern, log)
    if match:
        return Version(match.group(1))
    msg = "Version could not be found in bump log."
    raise RuntimeError(msg)


def get_current_version(path: pathlib.Path) -> Version:
    """Get current repository version."""
    stdout = io.StringIO()
    with (
        redirect_stdout(stdout),
        set_working_dir(path),
        set_system_args(["cz", "version", "--project"]),
    ):
        commitizen()
    base_version = stdout.getvalue()
    if not base_version:
        msg = "No version could be found."
        raise RuntimeError(msg)
    return Version(base_version)


def get_changelog(
    path: pathlib.Path, url: str, next_version: Version, changelog_template: str | None
) -> str:
    """Get changelog from commit history."""
    current_version = get_current_version(path)
    args = [
        "cz",
        "changelog",
        "--dry-run",
        "--unreleased-version",
        next_version.get_release_tag(),
    ]
    changelog_file = pathlib.Path(path) / "CHANGELOG.md"
    if current_version.get_release_tag() != "v0.0.0" and changelog_file.exists():
        args.extend(["--start-rev", current_version.get_release_tag()])
    stdout = io.StringIO()
    try:
        with (
            redirect_stdout(stdout),
            set_working_dir(path),
            set_system_args(args),
            set_changelog_template(path, url, args, changelog_template),
        ):
            commitizen()
    except DryRunExit:
        return stdout.getvalue()
    except Exception:
        raise
    else:
        msg = f"Expected {DryRunExit} exception was not raised."
        raise RuntimeError(msg)


def check(path: pathlib.Path, from_head: str, to_head: str) -> None:
    """Check commit messages formatting."""
    args = ["cz", "check", "--rev-range", f"{from_head}..{to_head}"]
    with (
        set_working_dir(path),
        set_system_args(args),
    ):
        commitizen()
