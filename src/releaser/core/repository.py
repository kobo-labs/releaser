"""Module for interacting with a Git repository."""

import pathlib
import re

import git

GitRef = git.Head | git.TagReference | git.RemoteReference | git.Reference


class GitRepository:
    """Class for interacting with an existing Git repository."""

    def __init__(self, path: pathlib.Path) -> None:
        """Initialize the GitRepository with the path to an existing repository."""
        self.repo = git.Repo(path)
        if "main" in self.repo.remote().refs:
            self.default_branch = "main"
        elif "master" in self.repo.remote().refs:
            self.default_branch = "master"
        else:
            msg = "Default branch not found."
            raise ValueError(msg)

    def _get_remote_refs(self) -> list[git.RemoteReference]:
        """Get all remote references."""
        return self.repo.remote().refs

    def find_release_branches(self) -> list[str]:
        """Find all release branches on the origin remote."""
        pattern = re.compile(r"origin/v\d+")

        def extract_number(branch: str) -> int:
            match = re.search(r"\d+", branch)
            return int(match.group()) if match else -1

        release_branches = [
            branch.name.replace("origin/", "")
            for branch in self._get_remote_refs()
            if pattern.match(branch.name)
        ]

        return sorted(release_branches, key=extract_number, reverse=True)

    def _remote(self, branch_name: str) -> str:
        """Format a branch name with the remote name."""
        return f"{self.repo.remote().name}/{branch_name}"

    def find_first_commit(self) -> git.Commit:
        """Find the first commit in the default branch."""
        return next(
            self.repo.iter_commits(rev=self._remote(self.default_branch), max_parents=0)
        )

    def get_workdir(self) -> pathlib.Path:
        """Get the working directory of the repository."""
        return pathlib.Path(str(self.repo.working_tree_dir))

    def _checkout_clean(self, head: GitRef | git.HEAD) -> None:
        if isinstance(head, GitRef):
            head.checkout()
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.git.clean("-fd")

    def checkout(self, branch: str, on_branch: str = "HEAD") -> None:
        """Checkout a branch or create and checkout a new branch based on 'on'."""
        head_ref = self.find_reference(branch)
        if isinstance(head_ref, git.RemoteReference):
            name = head_ref.name.replace("origin/", "")
            head = self.repo.create_head(name, head_ref)
            head.set_tracking_branch(head_ref)
            self._checkout_clean(head)
        elif isinstance(head_ref, git.Head):
            self._checkout_clean(head_ref)
        else:
            on_reference = self.find_reference(on_branch)
            if on_reference:
                head = self.repo.create_head(branch, on_reference)
            else:
                head = self.repo.create_head(branch, on_branch)
            self._checkout_clean(head)

    def find_reference(self, branch: str) -> GitRef | None:
        """Find and return a branch reference."""
        if branch == "HEAD":
            return self.repo.head.reference
        if branch in self.repo.branches:
            return self.repo.branches[branch]
        if branch in self.repo.remote().refs:
            return self.repo.remote().refs[branch]
        return None

    def commit(self, files: list[pathlib.Path], message: str) -> git.Commit:
        """Commit the specified files with a message."""
        self.repo.index.add(files)  # type: ignore[reportUnknownMemberType]
        return self.repo.index.commit(message)

    def tag(self, tag: str, message: str, commit: git.Commit) -> git.TagReference:
        """Create an annotated tag for a commit."""
        return self.repo.create_tag(tag, str(commit), message)

    def merge(
        self, source_branch: str, target_branch: str, message: str | None = None
    ) -> None:
        """Merge a source branch into a target branch."""
        source_reference = self.find_reference(source_branch)
        if not source_reference:
            msg = "Could not find source branch head."
            raise RuntimeError(msg)

        target_reference = self.find_reference(target_branch)
        if not target_reference:
            msg = "Could not find target branch head."
            raise RuntimeError(msg)

        self._checkout_clean(target_reference)
        merge_base = self.repo.merge_base(source_reference, target_reference)
        self.repo.index.merge_tree(source_reference, base=merge_base)
        if not message:
            message = f"Merge `{source_branch}` into `{target_branch}`"
        self.repo.index.commit(
            message,
            parent_commits=[target_reference.commit, source_reference.commit],
        )
        self._checkout_clean(self.repo.head)

    def push(self, ref_names: list[str], *, dry_run: bool) -> None:
        """Push the references identified by their names to the origin remote."""
        self.repo.remote().push(ref_names, dry_run=dry_run)

    def delete(self, branch: str) -> None:
        """Delete the specified branch after checking out the default branch."""
        if branch not in self.repo.heads:
            return
        default_branch = self.find_reference(self.default_branch)
        if default_branch:
            self._checkout_clean(default_branch)
            self.repo.delete_head(branch, force=True)

    def get_url(self) -> str:
        """Get remote URL."""
        return self.repo.remote().url
