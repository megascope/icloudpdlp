# iCloud Photos Download Processor

Apple lets you download all your icloud photos in archive zip files, however it just gives you a bunch of directories full of files and some CSVs with metadata in a disorganized mess. This utility processes the CSV files and photos into organized directories, setting file attributes to match EXIF metadata.

In order to use the tool you will need to be able to use the macOS terminal and command line utilities.

## Dependencies
This tool requires the command line `exiftool` (https://exiftool.org/) by Phil Harvey. It can be installed on most systems and is capable of reading tags from images and movies alike.

## How to get the archives
Instructions as of January 2026
1. Got to https://privacy.apple.com.
2. Go to "Request a copy of your data"
3. Select iCloud Photos, then continue
4. Select the largest size you can comfortably download (5GB+ for large libraries)
5. Select "Complete Request"
6. Wait around 5 days
7. You will get an email saying your download request is complete. Download all the files to one directory.
8. Uncompress the archives (see below)
9. Run this tool.

## How to uncompress the archives
Apple seems to put zip files inside of zip files. From the directory you have the zip archives first uncompress the originals, assumes you already have the `unzip` CLI installed.

```
for i in *.zip; do
    UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip "$i"
done
```

This creates a bunch of directories called `iCloud Photos Part 1 of 10`, some of which have additional zip files.

Now extract all the secondary zip files

```
for dir in "iCloud Photos Part "*; do
  if [ -d "$dir" ]; then
    cd "$dir" || exit
    for zip in *.zip; do
      UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip "$zip"
    done
    cd ..
  fi
done
```

You are now ready to run this utility.

## Usage

Examples

Process directories 3 and 4, with verbose logging, outputing files to `~/done`
```
icloudpdlp --source ~/iCloud\ Photos\ Part\ [34]\ of\ 10/ -v --output ~/done
```

Process directory 1, only file ABCD.HEIC outputing files to `~/done`
```
icloudpdlp --source ~/iCloud\ Photos\ Part\ 1\ of\ 10/ --include ABCD.HEIC --output ~/done
```

Process directory 2, do not make and changes but print what would be done (dry run)
```
icloudpdlp --source ~/iCloud\ Photos\ Part\ 2\ of\ 10/ -n
```

## Developing

Clone the repo
```
cd icloudpdlp
python3 -m venv .venv
source .venv/bin/activate

# install build tools
pip install build

# install this utility
pip install -e ".[dev]"

# edit code and run with
icloudpdlp

# run tests
pytest
```
