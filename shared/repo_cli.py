import argparse
import os
import sys


def add_repo_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-path",
        metavar="PATH",
        help="Path to the target repository (sets/overrides REPO_PATH for this run).",
    )


def resolve_repo_path(cli_value: str | None) -> str:
    from shared.paths import get_repo_path

    if cli_value:
        os.environ["REPO_PATH"] = os.path.abspath(os.path.expanduser(cli_value))
    try:
        return get_repo_path()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
