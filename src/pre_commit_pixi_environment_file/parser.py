import argparse


def get_parser() -> argparse.ArgumentParser:
    """Create an ArgumentParser for the compare_environments function."""
    parser = argparse.ArgumentParser(
        description="Compare and update environment files using pixi data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--root-dir", type=str, default=".", help="Path to the root directory"
    )

    parser.add_argument(
        "--environment-file",
        type=str,
        default="environment.yml",
        help="Name of the environment file",
    )

    parser.add_argument(
        "--explicit",
        action="store_true",
        default=False,
        help="Use explicit package specifications",
    )

    parser.add_argument(
        "--name", type=str, default=None, help="Environment name (optional)"
    )

    parser.add_argument(
        "--prefix", type=str, default=None, help="Environment prefix path (optional)"
    )

    parser.add_argument(
        "--include-pip-packages",
        action="store_true",
        default=False,
        help="Include pip packages in the environment",
    )

    parser.add_argument(
        "--no-include-conda-channels",
        action="store_false",
        dest="include_conda_channels",
        default=True,
        help="Exclude conda channels from the environment (default: include channels)",
    )

    parser.add_argument(
        "--include-build",
        action="store_true",
        default=False,
        help="Include build information",
    )

    return parser
