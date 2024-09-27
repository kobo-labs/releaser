"""Expose release package to command line."""

import logging
import sys

from . import cli


def main() -> None:
    """Entrypoint for Nix."""
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    cli.main(cli.parse(sys.argv[1:]))


if __name__ == "__main__":
    main()
