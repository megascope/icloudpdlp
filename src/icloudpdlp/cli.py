"""Command-line interface for iCloud Photos Download Processor."""

import argparse
import sys
import csv
import exiftool

from pathlib import Path

import hashlib
import base64

# Constants
DIR_PHOTOS = "Photos"
DIR_SHARED_ALBUMS = "iCloud Shared Albums"
FILE_PHOTOS_CSV = "Photo Details"
FILE_SHARED_ALBUMS_CSV = "Shared Library Details"
CSV_EXT = ".csv"

# Contents of the CSV files
COL_IMG_NAME = "imgName"
COL_CHECKSUM = "fileChecksum"
COL_CREATED_DATE = "originalCreationDate"
COL_IMPORT_DATE = "importDate"
COL_BY_ME = "contributedByMe"
COL_DELETED = "deleted"

VAL_YES = "yes"
VAL_NO = "no"

def calculate_file_checksum(file_path):
    """Calculate various checksums for comparison."""
    with open(file_path, 'rb') as f:
        data = f.read()

    # SHA-1 (20 bytes → 28 chars base64)
    sha1 = base64.b64encode(hashlib.sha1(data).digest()).decode('utf-8')

    # MD5 (16 bytes → 24 chars base64) - less likely but possible
    md5 = base64.b64encode(hashlib.md5(data).digest()).decode('utf-8')

    # SHA-256 (32 bytes → 44 chars base64) - probably too long
    sha256 = base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')

    # Also try hex encoding in case it's not base64
    sha1_hex = hashlib.sha1(data).hexdigest()
    md5_hex = hashlib.md5(data).hexdigest()

    print(f"SHA-1 (base64): {sha1}")
    print(f"MD5 (base64):   {md5}")
    print(f"SHA-256 (base64): {sha256}")
    print(f"SHA-1 (hex):    {sha1_hex}")
    print(f"MD5 (hex):      {md5_hex}")

def xcalculate_file_checksum(file_path):
    """Calculate SHA-1 checksum of a file and return it in base64 format."""
    sha1 = hashlib.sha1()

    # Read file in chunks to handle large files efficiently
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha1.update(chunk)

    # Return base64-encoded SHA-1 hash
    return base64.b64encode(sha1.digest()).decode('utf-8')


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"


def info(*args, **kwargs):
    """Print info message in cyan color."""
    print(f"{Colors.BOLD}", end="")
    print(*args, **kwargs, end="")
    print(Colors.RESET)

def warn(*args, **kwargs):
    """Print warning message in yellow color."""
    print(f"{Colors.YELLOW}", end="")
    print(*args, **kwargs, end="")
    print(Colors.RESET)

def debug(*args, **kwargs):
    """Print debug message in gray color."""
    print(f"{Colors.GRAY}", end="")
    print(*args, **kwargs, end="")
    print(Colors.RESET)

def error(*args, **kwargs):
    """Print error message in red color."""
    print(f"{Colors.RED}", end="")
    print(*args, **kwargs, end="")
    print(Colors.RESET)
    raise Exception("Error occurred, exiting.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Process and organize iCloud Photos archives",
        prog="icloudpdlp"
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Directory containing uncompressed iCloud Photos archives, including the 'Photos' and 'iCloud Shared Albums' directories"
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=False,
        help="Directory where organized photos will be saved"
    )

    parser.add_argument(
        "--skip-personal-library",
        action="store_true",
        help="Do not process photos from the Personal Library",
    )

    parser.add_argument(
        "--skip-shared-library",
        action="store_true",
        help="Do not process photos from the Shared Library",
    )

    parser.add_argument(
        "--validate-checksums",
        action="store_true",
        help="Validate iCloud checksums"
    )

    parser.add_argument(
        "-y", "--overwrite",
        action="store_true",
        help="No confirmation prompts, overwrite existing files without asking"
    )

    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Make no changes, just print what would be done"
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

    if not args.output:
        warn(f"No output directory specified, assuming --dry-run mode")
        args.dry_run = True

    if args.verbose:
        info("Verbose mode enabled")

    photos_path = args.source / DIR_PHOTOS
    if photos_path.exists():
        process_photos(photos_path, args)
    else:
        warn(f"Photos directory not found at {photos_path}, are you running from the unzipped root?")

    return 0


def process_photos(photos_path, args):
    csv_files = photos_path.glob(f"{FILE_PHOTOS_CSV}*{CSV_EXT}")

    files = {}

    for csv_file in csv_files:
        if csv_file.name.startswith(FILE_PHOTOS_CSV):
            info(f"Processing {csv_file.name}...")
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # row is a dictionary with column headers as keys
                    if args.verbose: debug(row)
                    filename = row[COL_IMG_NAME]
                    if filename in files:
                        warn(f"Duplicate filename {filename} found in {csv_file.name}, skipping")
                        continue

                    if row[COL_DELETED] == VAL_YES:
                        warn(f"File {filename} is marked as deleted, skipping")
                        continue

                    if args.validate_checksums:
                        info(f"Validating checksum for {filename}...")
                        file_path = photos_path / filename
                        if not file_path.exists():
                            error(f"File {filename} not found in {photos_path}, skipping checksum validation")

                        calculated_checksum = calculate_file_checksum(file_path)
                        if calculated_checksum != row[COL_CHECKSUM]:
                            error(f"Checksum mismatch for {filename}: expected {row[COL_CHECKSUM]}, got {calculated_checksum}")

                    files[filename] = row


if __name__ == "__main__":
    sys.exit(main())
