"""Module for creating a new release in a git repository."""

import logging
import pathlib

from .core import repository
from .core.version import Version

logger = logging.getLogger(__name__)


def prepare_release_branch(
    repo: repository.GitRepository, next_release_branch: str
) -> None:
    """Prepare release branch for new release."""
    release_branches = repo.find_release_branches()
    if release_branches:
        if release_branches[0] == next_release_branch:
            logger.info("Checkout existing release branch '%s'.", release_branches[0])
            repo.checkout(release_branches[0])
        else:
            logger.info(
                "Checkout new release branch '%s' on previous release branch '%s'.",
                next_release_branch,
                release_branches[0],
            )
            repo.checkout(next_release_branch, release_branches[0])
    else:
        first_commit = repo.find_first_commit()
        logger.info(
            "Checkout new release branch '%s' on first commit '%s'.",
            next_release_branch,
            first_commit,
        )
        repo.checkout(next_release_branch, str(first_commit))


def write_changelog(repo: repository.GitRepository, changelog: str) -> None:
    """Write changelog into file."""
    changelog_file = repo.get_workdir() / "CHANGELOG.md"

    previous_changelog = ""
    if changelog_file.exists():
        with changelog_file.open(mode="r") as f:
            previous_changelog = f.read()

    next_changelog = changelog
    if previous_changelog:
        next_changelog = f"{next_changelog}\n{previous_changelog}"

    with changelog_file.open(mode="w") as f:
        f.write(next_changelog)


def release(
    repo: repository.GitRepository,
    source_branch: str,
    next_version: Version,
    changelog: str,
    *,
    dry_run: bool,
) -> None:
    """Release a new version to a release branch."""
    next_release_branch = next_version.get_release_branch()
    next_release_tag = next_version.get_release_tag()
    prepare_release_branch(repo, next_release_branch)
    logger.info(
        "Merge source branch '%s' into release branch '%s'.",
        source_branch,
        next_release_branch,
    )
    repo.merge(source_branch, next_release_branch)
    logger.info("Update CHANGELOG for '%s'.", next_release_tag)
    write_changelog(repo, changelog)
    release_commit = repo.commit(
        [pathlib.Path("CHANGELOG.md")], f"Update CHANGELOG for {next_release_tag}"
    )
    logger.info(
        "Created annotated tag '%s' on commit '%s'.", next_release_tag, release_commit
    )
    repo.tag(
        next_release_tag, f"Automated release of {next_release_tag}", release_commit
    )
    logger.info(
        "Push branch '%s' and tag '%s' to origin.",
        next_release_branch,
        next_release_tag,
    )
    repo.push([next_release_branch, next_release_tag], dry_run=dry_run)
