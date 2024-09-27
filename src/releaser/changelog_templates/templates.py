"""Module for handling templates files."""

import importlib.resources
from pathlib import Path


def get_template_file(changelog_template: str) -> str:
    """Get path to changelog template file."""
    template_file = importlib.resources.files(__package__).joinpath(changelog_template)
    return str(template_file)


def get_all_templates() -> list[str]:
    """Return list of all templates file names."""
    package_files = importlib.resources.files(__package__)
    return [
        file.name
        for file in package_files.iterdir()
        if file.is_file() and Path(str(file)).suffix == ".j2"
    ]
