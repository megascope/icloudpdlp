"""Tests for the CLI module."""

import pytest
import datetime
from pathlib import Path
from icloudpdlp.cli import main, figure_out_createdate, include_file_function


def test_main_help(capsys, monkeypatch):
    """Test that --help works."""
    monkeypatch.setattr("sys.argv", ["icloudpdlp", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Process and organize iCloud Photos archives" in captured.out

class TestFigureOutCreateDate:
    """Tests for the figure_out_createdate function."""

    def test_subsec_datetime_original_with_subseconds(self):
        """Test SubSecDateTimeOriginal with subseconds."""
        exifdata = {
            "EXIF:SubSecDateTimeOriginal": "2021:03:26 16:25:20.236-07:00"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, 236000, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
        assert result == expected

    def test_subsec_datetime_original_without_subseconds(self):
        """Test SubSecDateTimeOriginal without subseconds."""
        exifdata = {
            "EXIF:SubSecDateTimeOriginal": "2021:03:26 16:25:20-07:00"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
        assert result == expected

    def test_datetime_original_with_offset(self):
        """Test DateTimeOriginal with OffsetTimeOriginal."""
        exifdata = {
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20",
            "EXIF:OffsetTimeOriginal": "-07:00"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
        assert result == expected

    def test_datetime_original_with_offsettime_fallback(self):
        """Test DateTimeOriginal with OffsetTime (fallback when OffsetTimeOriginal not available)."""
        exifdata = {
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20",
            "EXIF:OffsetTime": "+05:30"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        assert result == expected

    def test_datetime_original_with_z_offset(self):
        """Test DateTimeOriginal with 'Z' offset (UTC)."""
        exifdata = {
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20",
            "EXIF:OffsetTimeOriginal": "Z"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_datetime_original_without_offset(self):
        """Test DateTimeOriginal without offset (assumes UTC)."""
        exifdata = {
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_creation_date_with_offset(self):
        """Test CreationDate with offset."""
        exifdata = {
            "QuickTime:CreationDate": "2024:10:13 08:30:39-05:00"
        }
        result = figure_out_createdate(Path("test.mov"), "Sunday October 13,2024 1:30 PM GMT", exifdata)
        expected = datetime.datetime(2024, 10, 13, 8, 30, 39, tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        assert result == expected

    def test_createdate_without_offset(self):
        """Test CreateDate without offset (assumes UTC)."""
        exifdata = {
            "EXIF:CreateDate": "2021:03:26 16:25:20"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_fallback_to_apple_date(self):
        """Test fallback to Apple date when no EXIF dates are available."""
        exifdata = {}
        result = figure_out_createdate(Path("test.jpg"), "Sunday August 13,2023 3:09 PM GMT", exifdata)
        expected = datetime.datetime(2023, 8, 13, 15, 9, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_priority_subsec_over_datetime_original(self):
        """Test that SubSecDateTimeOriginal takes priority over DateTimeOriginal."""
        exifdata = {
            "EXIF:SubSecDateTimeOriginal": "2021:03:26 16:25:20.236-07:00",
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20",
            "EXIF:OffsetTimeOriginal": "+05:00"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        # Should use SubSecDateTimeOriginal with -07:00, not DateTimeOriginal with +05:00
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, 236000, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
        assert result == expected

    def test_multiple_exif_tags_same_name(self):
        """Test handling of multiple EXIF tags with same name from different namespaces."""
        exifdata = {
            "EXIF:DateTimeOriginal": "2021:03:26 16:25:20",
            "XMP:DateTimeOriginal": "2020:01:01 10:00:00",
            "EXIF:OffsetTimeOriginal": "-07:00"
        }
        result = figure_out_createdate(Path("test.jpg"), "Sunday March 26,2021 4:25 PM GMT", exifdata)
        # Should find the first DateTimeOriginal (EXIF)
        expected = datetime.datetime(2021, 3, 26, 16, 25, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
        assert result == expected

class TestIncludeFileFunction:
    """Tests for the include_file_function."""

    def test_single_pattern_match(self):
        """Test matching with a single pattern."""
        include_func = include_file_function([r'\.jpg$'])
        assert include_func("photo.jpg") is True
        assert include_func("photo.png") is False

    def test_multiple_patterns_match_first(self):
        """Test matching first pattern when multiple patterns provided."""
        include_func = include_file_function([r'\.jpg$', r'\.png$', r'\.gif$'])
        assert include_func("photo.jpg") is True

    def test_multiple_patterns_match_middle(self):
        """Test matching middle pattern when multiple patterns provided."""
        include_func = include_file_function([r'\.jpg$', r'\.png$', r'\.gif$'])
        assert include_func("photo.png") is True

    def test_multiple_patterns_match_last(self):
        """Test matching last pattern when multiple patterns provided."""
        include_func = include_file_function([r'\.jpg$', r'\.png$', r'\.gif$'])
        assert include_func("photo.gif") is True

    def test_no_match(self):
        """Test when filename doesn't match any pattern."""
        include_func = include_file_function([r'\.jpg$', r'\.png$'])
        assert include_func("document.pdf") is False

    def test_pattern_matches_anywhere(self):
        """Test that pattern matches anywhere in filename (search behavior)."""
        include_func = include_file_function([r'vacation'])
        assert include_func("vacation_2024.jpg") is True
        assert include_func("photos_vacation.jpg") is True
        assert include_func("my_vacation_photo.jpg") is True
        assert include_func("work_photo.jpg") is False

    def test_case_sensitive_matching(self):
        """Test that pattern matching is case-sensitive by default."""
        include_func = include_file_function([r'\.JPG$'])
        assert include_func("photo.JPG") is True
        assert include_func("photo.jpg") is False

    def test_case_insensitive_pattern(self):
        """Test case-insensitive matching with explicit flag."""
        include_func = include_file_function([r'(?i)\.jpg$'])
        assert include_func("photo.jpg") is True
        assert include_func("photo.JPG") is True
        assert include_func("photo.Jpg") is True

    def test_complex_regex_pattern(self):
        """Test with complex regex patterns."""
        include_func = include_file_function([r'IMG_\d{4}\.jpg$'])
        assert include_func("IMG_1234.jpg") is True
        assert include_func("IMG_5678.jpg") is True
        assert include_func("IMG_abcd.jpg") is False
        assert include_func("PHOTO_1234.jpg") is False

    def test_multiple_complex_patterns(self):
        """Test with multiple complex patterns."""
        include_func = include_file_function([
            r'IMG_\d{4}\.jpg$',
            r'VIDEO_\d{4}\.mov$',
            r'screenshot.*\.png$'
        ])
        assert include_func("IMG_1234.jpg") is True
        assert include_func("VIDEO_5678.mov") is True
        assert include_func("screenshot_2024.png") is True
        assert include_func("random_file.txt") is False

    def test_pattern_with_path(self):
        """Test pattern matching with full paths."""
        include_func = include_file_function([r'photos/.*\.jpg$'])
        assert include_func("photos/vacation.jpg") is True
        assert include_func("videos/vacation.jpg") is False

    def test_alternation_pattern(self):
        """Test pattern with alternation (|)."""
        include_func = include_file_function([r'\.(jpg|png|gif)$'])
        assert include_func("photo.jpg") is True
        assert include_func("photo.png") is True
        assert include_func("photo.gif") is True
        assert include_func("photo.bmp") is False

    def test_empty_pattern_list(self):
        """Test with empty pattern list (should match nothing)."""
        include_func = include_file_function([])
        assert include_func("any_file.jpg") is False
        assert include_func("another_file.txt") is False

    def test_pattern_with_special_chars(self):
        """Test pattern with special characters that need escaping."""
        include_func = include_file_function([r'file\(1\)\.jpg$'])
        assert include_func("file(1).jpg") is True
        assert include_func("file1.jpg") is False

    def test_match_all_pattern(self):
        """Test pattern that matches everything."""
        include_func = include_file_function([r'.*'])
        assert include_func("any_file.jpg") is True
        assert include_func("document.pdf") is True
        assert include_func("video.mov") is True


# TODO: Add more tests for actual processing functionality
