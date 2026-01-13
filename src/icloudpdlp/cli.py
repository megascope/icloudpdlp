"""Command-line interface for iCloud Photos Download Processor."""

import argparse
import sys
import csv
import exiftool
import shutil
import os
import dateutil
from pathlib import Path
import datetime


# Constants
DIR_PHOTOS = "Photos"
DIR_SHARED_ALBUMS = "iCloud Shared Albums"
FILE_PHOTOS_CSV = "Photo Details"
FILE_SHARED_ALBUMS_CSV = "Shared Library Details"
CSV_EXT = ".csv"

# Contents of the CSV files
COL_IMG_NAME = "imgName"
COL_CHECKSUM = "fileChecksum" # This is a base64 encoded MMCS Hash, no documentation available to replicate
COL_CREATED_DATE = "originalCreationDate"
COL_IMPORT_DATE = "importDate"
COL_BY_ME = "contributedByMe"
COL_DELETED = "deleted"
COL_PY_PATH = "pyFilePath"
COL_PY_ISSHARED = "pyIsShared"
COL_PY_ITEMDATE = "pyCreateDate"
COL_PY_SKIP = "pySkip"

VAL_YES = "yes"
VAL_NO = "no"

EXIF_CREATEDATE = "CreateDate"
EXIF_SSCREATEDATE = "SubSecDateTimeOriginal"
EXIF_DTORIGINAL = "DateTimeOriginal"
EXIF_DTOFFSET = "OffsetTimeOriginal"
EXIF_OFFSET = "OffsetTime"
EXIF_CREATIONDATE = "CreationDate"

EXIFTAGS = [EXIF_CREATEDATE, EXIF_SSCREATEDATE, EXIF_DTORIGINAL, EXIF_DTOFFSET, EXIF_CREATIONDATE]

EXIF_HEADER = "EXIF:"
EXIF_SOURCEFILE = "SourceFile"

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
        help="Ignore photos from the Shared Library",
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
        "--output-directory-format",
        default="%Y/%m",
        help="Format for output directories, using strftime format codes. Default is %%Y/%%m (year/month/day)"
    )

    parser.add_argument(
        "--no-update-creationtime",
        action="store_true",
        help="Do not update the creation time of the output file to match EXIF CreateDate"
    )

    args = parser.parse_args()

    if not args.output:
        warn(f"No output directory specified, assuming --dry-run mode")
        args.dry_run = True
        args.output = Path()

    if args.verbose:
        info("Verbose mode enabled")

    photos_path = args.source / DIR_PHOTOS
    if photos_path.exists():
        process_photos(photos_path, args)
    else:
        warn(f"Photos directory not found at {photos_path}, are you running from the unzipped root?")

    return 0

def process_details(photos_path, files, args):
    csv_files = photos_path.glob(f"{FILE_PHOTOS_CSV}*{CSV_EXT}")
    for csv_file in csv_files:
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

                file_path = photos_path / filename
                if not file_path.exists():
                    warn(f"File {filename} not found in {photos_path}, skipping")
                    continue

                row[COL_PY_ISSHARED] = False
                row[COL_BY_ME] = None
                row[COL_PY_PATH] = file_path
                files[filename] = row

def process_shared(photos_path, files, args):
    csv_files = photos_path.glob(f"{FILE_SHARED_ALBUMS_CSV}*{CSV_EXT}")
    for csv_file in csv_files:
        info(f"Processing {csv_file.name}...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # row is a dictionary with column headers as keys
                if args.verbose: debug(row)
                filename = row[COL_IMG_NAME]

                frow = files.get(filename, None)
                if frow is None:
                    # should already have been found in details
                    warn(f"In shared but not detailed {filename} in {csv_file.name}, skipping")
                    continue

                frow[COL_PY_ISSHARED] = True
                frow[COL_BY_ME] = row[COL_BY_ME]


def get_first_tag_value(exifdata, tag_name):
    """Get the first value for a given tag name from the EXIF data."""
    for k, v in exifdata.items():
        if k.endswith(':' + tag_name):
            return v
    return None

def figure_out_createdate(file_path, appleDate, exifdata):
    create_date = None

    # this can get complex, there are multiple CreateDate and Offset values, not always consistent, especially with movies
    # we're aiming to get the earliest CreateDate that includes a time zone

    # first try SubSecDateTimeOriginal, format 2021:03:26 16:25:20.236-07:00
    tag = get_first_tag_value(exifdata, EXIF_SSCREATEDATE)
    if tag is not None:
        try:
            return datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S.%f%z")
        except ValueError:
            # sometimes there are no subseconds, try without them
            try:
                return datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S%z")
            except ValueError:
                # if that fails, fall back to the next method
                pass

    # try DateTimeOriginal + OffsetTimeOriginal, format 2021:03:26 16:25:20 +07:00
    tag = get_first_tag_value(exifdata, EXIF_DTORIGINAL)
    tag_offset = get_first_tag_value(exifdata, EXIF_DTOFFSET) or get_first_tag_value(exifdata, EXIF_OFFSET)
    if tag is not None:
        if tag_offset is not None:
            dt_str = f"{tag}{tag_offset}"
            return datetime.datetime.strptime(dt_str, "%Y:%m:%d H:%M:%S%z")
        else:
            # No offset, assume local time
            warn(f"{EXIF_DTORIGINAL} found without {EXIF_DTOFFSET} for {file_path}, assuming UTC")
            return datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)

    # try CreationDate, format 2024:10:13 08:30:39-05:00
    tag = get_first_tag_value(exifdata, EXIF_CREATIONDATE)
    if tag is not None:
        return datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S%z")

    # try CreateDate, format 2021:03:26 16:25:20, assume UTC
    tag = get_first_tag_value(exifdata, EXIF_CREATEDATE)
    if tag is not None:
        if tag_offset is not None:
            dt_str = f"{tag}{tag_offset}"
            return datetime.datetime.strptime(dt_str, "%Y:%m:%d H:%M:%S%z")
        else:
            warn(f"{EXIF_CREATEDATE} found for {file_path} without offset, assuming UTC")
            return datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)

    warn(f"No CreateDate found for {file_path}, using Apple Original Creation date instead")
    # apple dates are in format "Sunday August 13,2023 3:09 PM GMT"
    # dateutil.parser can't quite handle this format, we just need to replace the comma with a space
    create_date = dateutil.parser.parse(appleDate.replace(",", " "))

    return create_date


def process_photos(photos_path, args):
    files = {}
    process_details(photos_path, files, args)
    process_shared(photos_path, files, args)

    # get all the files in the directory, everything but CSVS
    for file_path in photos_path.iterdir():
        if file_path.is_file() and file_path.suffix != CSV_EXT:
            filename = file_path.name
            if filename not in files:
                warn(f"File {filename} found in {photos_path} but not in any details, adding to processing list")
                frow = {}
                # set some defaults so the rest of the processing works
                frow[COL_PY_ISSHARED] = False
                frow[COL_PY_PATH] = file_path
                frow[COL_CREATED_DATE] = datetime.datetime.fromtimestamp(file_path.stat().st_ctime, tz=datetime.timezone.utc).isoformat()
                files[filename] = frow

    # now remove files we are not going to process based on the skip flags
    metadata_files = []
    for f in files.values():
        if f[COL_PY_ISSHARED]:
            if args.skip_shared_library:
                info(f"Skipping shared library file {f[COL_PY_PATH].name}")
                f[COL_PY_SKIP] = True
                continue
        elif args.skip_personal_library:
                info(f"Skipping personal library file {f[COL_PY_PATH].name}")
                f[COL_PY_SKIP] = True
                continue

        f[COL_PY_SKIP] = False
        metadata_files.append(f[COL_PY_PATH].as_posix())

    with exiftool.ExifToolHelper() as et:
        # all these creation dates exist, some might have GMT offsets
        for exifdata in et.get_tags(metadata_files, tags=EXIFTAGS):
            if args.verbose: debug(exifdata)
            fullpath = exifdata[EXIF_SOURCEFILE]
            filename = Path(fullpath).name

            frow = files.get(filename, None)
            if frow is None:
                warn(f"ExifTool Source {fullpath} -> {filename} not found in details, skipping")
                continue

            create_date = figure_out_createdate(frow[COL_PY_PATH], frow[COL_CREATED_DATE], exifdata)

            if (args.verbose): debug(f"Setting CreateDate for {filename} to {create_date} tz = {create_date.tzinfo}")
            frow[COL_PY_ITEMDATE] = create_date

    # got all files and creation dates, now queue actions

    # make output directories
    for frow in files.values():
        if frow[COL_PY_SKIP]: continue

        createdate = frow[COL_PY_ITEMDATE]
        output_dir = args.output / ("Shared" if frow[COL_PY_ISSHARED] else "Personal") / createdate.strftime(args.output_directory_format)
        if not args.dry_run: output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / frow[COL_PY_PATH].name
        if output_file.exists() and not args.overwrite:
            warn(f"Output file {output_file} already exists, skipping")
            continue

        if not args.dry_run:
            shutil.copy2(frow[COL_PY_PATH], output_file)
            if not args.no_update_creationtime:
                os.utime(output_file, (createdate.timestamp(), createdate.timestamp()))

        info(f"{frow[COL_PY_PATH].name} -> {output_file} { "[no creation change]" if args.no_update_creationtime else "[creation time updated]" }")

if __name__ == "__main__":
    sys.exit(main())
