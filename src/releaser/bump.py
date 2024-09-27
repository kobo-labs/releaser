"""Module for checking for a version bump."""

import logging
import uuid

from commitizen.exceptions import NoneIncrementExit

from .core import commits
from .core.repository import GitRepository
from .core.version import Version

logger = logging.getLogger(__name__)


def bump(
    repo: GitRepository, source: str, changelog_template: str | None
) -> tuple[Version | None, str | None]:
    """Check if repository version can be bumped."""
    temp_branch = str(uuid.uuid4())
    try:
        release_branches = repo.find_release_branches()
        logger.info("Release branches found: %s", release_branches)
        if release_branches:
            logger.info(
                "Check out temporary branch '%s' on '%s'",
                temp_branch,
                release_branches[0],
            )
            repo.checkout(temp_branch, release_branches[0])
            logger.info("Merging '%s' into '%s'", source, temp_branch)
            repo.merge(source, temp_branch)
        workdir = repo.get_workdir()
        logger.info("Reading changelog from '%s'.", workdir)
        url = repo.get_url()
        logger.info("Linking to '%s'.", url)
        next_version = commits.bump(workdir)
        changelog = commits.get_changelog(
            workdir,
            url,
            next_version,
            changelog_template,
        )
    except NoneIncrementExit:
        logger.info("Could not find commits triggering new version.")
        return None, None
    except Exception:
        raise
    else:
        logger.info("Next version: %s", next_version.version.base_version)
        logger.info(changelog)
        return next_version, changelog
    finally:
        logger.info("Delete temporary branch '%s'", temp_branch)
        repo.delete(temp_branch)
