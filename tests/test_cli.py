"""Tests for the CLI module."""

import pytest
from pathlib import Path
from icloudpdp.cli import main


def test_main_help(capsys, monkeypatch):
    """Test that --help works."""
    monkeypatch.setattr("sys.argv", ["icloudpdp", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Process and organize iCloud Photos archives" in captured.out


def test_main_version(capsys, monkeypatch):
    """Test that --version works."""
    monkeypatch.setattr("sys.argv", ["icloudpdp", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


# TODO: Add more tests for actual processing functionality
