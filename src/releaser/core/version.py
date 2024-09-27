"""Module to interact with versions."""

from packaging.version import Version as SemVer


class Version:
    """Interact with semantic version."""

    def __init__(self, base_version: str) -> None:
        """Initialize from base version string."""
        self.version = SemVer(base_version)

    def get_release_branch(self) -> str:
        """Get release branch from semantic version."""
        return f"v{self.version.major}"

    def get_release_tag(self) -> str:
        """Get release tag from semantic version."""
        return f"v{self.version.base_version}"
