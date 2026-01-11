"""Command-line interface for iCloud Photos Download Processor."""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Process and organize iCloud Photos archives",
        prog="icloudpdp"
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing uncompressed iCloud Photos archives"
    )

    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where organized photos will be saved"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    # TODO: Implement processing logic
    print(f"Processing photos from: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")

    if args.verbose:
        print("Verbose mode enabled")

    return 0


if __name__ == "__main__":
    sys.exit(main())
