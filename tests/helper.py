import argparse
import os
import pathlib
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import git
from jinja2 import Environment, FileSystemLoader

from src.releaser import cli

COMMIT_URL = "https://github.com/organization/repository-git"
CZ_JSON = """
{
    "commitizen": {
        "name": "cz_conventional_commits",
        "tag_format": "v$version",
        "version_scheme": "semver",
        "version_provider": "scm",
        "update_changelog_on_bump": true
    }
}
"""
RESOURCES_DIR = pathlib.Path(__file__).parent / "resources"


class Origin:
    """
    Simulates a git remote origin for testing purposes.

    Sets up an origin in a separate local directory.
    Provides a clone() method similar to 'git clone'.
    Provides a commit() method to commit directly to the origin.
    """

    def __init__(
        self,
        base_dir: pathlib.Path,
        default_branch: str = "main",
        additional_branches: list[str] | None = None,
    ) -> None:
        base_dir.mkdir(exist_ok=True)
        self.base_dir = base_dir
        self.default_branch = default_branch
        self.origin_dir = base_dir / "origin"
        self.origin_repo = self._init_origin()
        self._setup_default_branch()
        if additional_branches:
            for branch in additional_branches:
                self.create_branch(branch)

    def _init_origin(self) -> git.Repo:
        self.origin_dir.mkdir()
        return git.Repo.init(self.origin_dir, bare=True)

    def _setup_default_branch(self) -> None:
        setup_dir = self.base_dir / "setup"
        setup_dir.mkdir()
        repo = git.Repo.init(setup_dir)
        self._commit_file(repo, "README.md", "# test", "first commit")
        repo.heads[0].rename(self.default_branch)
        repo.create_remote("origin", self.origin_dir).push(self.default_branch)

    def create_branch(self, branch_name: str, base: str = "HEAD") -> None:
        repo = self.clone()
        repo.create_head(branch_name, base)
        repo.remotes.origin.push(branch_name)

    @staticmethod
    def _commit_file(
        repo: git.Repo, file_name: str, content: str, message: str
    ) -> git.Commit:
        file_path = pathlib.Path(repo.working_tree_dir) / file_name
        file_path.write_text(content)
        repo.index.add([file_path])
        return repo.index.commit(message)

    def clone(self, branches: list[str] | None = None) -> git.Repo:
        clone_dir = self.base_dir / str(uuid.uuid4())
        clone_dir.mkdir()
        repo = git.Repo.init(clone_dir)
        origin = repo.create_remote("origin", self.origin_dir)
        origin.fetch()
        branches = branches or [self.default_branch]
        for branch in branches:
            repo.create_head(branch, origin.refs[branch]).set_tracking_branch(
                origin.refs[branch]
            ).checkout()
        return repo

    def commit(
        self, file_name: str, content: str, message: str, branch: str | None = None
    ) -> git.Commit:
        branch = branch or self.default_branch
        repo = self.clone([branch])
        commit = self._commit_file(repo, file_name, content, message)
        repo.remotes.origin.push(branch)
        return commit

    def delete(self, file_name: str, message: str, branch: str | None = None) -> None:
        branch = branch or self.default_branch
        repo = self.clone([branch])
        file_path = pathlib.Path(repo.working_tree_dir) / file_name
        file_path.unlink()
        repo.index.remove([file_path])
        repo.index.commit(message)
        repo.remotes.origin.push(branch)


class ExpectedChangelog:
    def __init__(
        self, resource_dir: pathlib.Path = RESOURCES_DIR, commit_url: str = COMMIT_URL
    ) -> None:
        self.env = Environment(loader=FileSystemLoader(resource_dir), autoescape=True)
        self.context = {}
        self.context["commit_url"] = f"{commit_url}/commit/"

    def add(self, key: str, value: str) -> "ExpectedChangelog":
        self.context[key] = value
        return self

    def render(self, template_file: str) -> str:
        template = self.env.get_template(template_file)
        return template.render(self.context)


def git_graph(repo_path: pathlib.Path) -> str:
    return subprocess.run(
        [
            "/usr/bin/git",
            "log",
            "--graph",
            "--oneline",
            "--all",
            "--decorate",
            "--pretty=format:%s%C(auto)%d%C(reset)",
        ],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def parse_github_output(github_output_path: pathlib.Path) -> dict[str, str]:
    """
    Parse the GitHub output file into a dictionary.

    Parameters:
    github_output_path (Path): The path to the GitHub output file.

    Returns:
    dict: A dictionary containing the parsed key-value pairs.
    """
    output_dict = {}
    output_text = github_output_path.read_text()
    for line in output_text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            output_dict[key] = value
    return output_dict


@contextmanager
def temporary_env(variables: dict[str, str]) -> Iterator[None]:
    original_env = os.environ.copy()
    os.environ.update(variables)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def run_releaser(
    tmp_path: pathlib.Path,
    repository: pathlib.Path,
    action: str = "release",
    source: str = "main",
    dry_run: bool = False,
) -> None:
    args = argparse.Namespace
    args.repository = repository
    args.source = source
    args.dry_run = dry_run
    args.action = action
    args.changelog_template = "github_linked_sha.md.j2"

    env_vars = {
        "GITHUB_OUTPUT": str(tmp_path / "github_output.txt"),
        "RUNNER_TEMP": str(tmp_path),
    }

    with temporary_env(env_vars):
        cli.main(args)
