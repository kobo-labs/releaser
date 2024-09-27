"""Module for checking commit messages."""

import logging

from .core import commits, repository

TO_HEAD = "HEAD"


logger = logging.getLogger(__name__)


def check(repo: repository.GitRepository, from_ref_name: str) -> None:
    """Check commit messages from range head to head."""
    from_reference = repo.find_reference(from_ref_name)
    if not from_reference:
        msg = f"Could not find branch '{from_ref_name}'."
        raise ValueError(msg)
    if from_reference.is_remote():
        from_branch = f"{from_reference.remote_name}/{from_reference.remote_head}"
    else:
        from_branch = from_reference.name

    commits.check(repo.get_workdir(), from_branch, TO_HEAD)
