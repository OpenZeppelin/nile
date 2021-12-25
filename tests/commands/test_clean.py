"""Tests for clean command."""
from pathlib import Path
from unittest.mock import patch

import pytest

from nile.commands.clean import clean_command
from nile.common import (
    ACCOUNTS_FILENAME,
    BUILD_DIRECTORY,
    DEPLOYMENTS_FILENAME,
)


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@patch("nile.commands.clean.shutil.rmtree")
@patch("nile.commands.clean.os.remove")
def test_clean_command_already_clean(mock_os_remove, mock_shutil_rmtree):
    clean_command()
    mock_os_remove.assert_not_called()
    mock_shutil_rmtree.assert_not_called()


@pytest.mark.parametrize(
    "fname",
    [
        f"localhost.{ACCOUNTS_FILENAME}",
        f"localhost.{DEPLOYMENTS_FILENAME}",
    ],
)
@patch("nile.commands.clean.shutil.rmtree")
@patch("nile.commands.clean.os.remove")
def test_clean_command_clean_files(mock_os_remove, mock_shutil_rmtree, fname):
    Path(fname).touch()
    clean_command()
    mock_os_remove.assert_called_once_with(fname)
    mock_shutil_rmtree.assert_not_called()


@patch("nile.commands.clean.shutil.rmtree")
@patch("nile.commands.clean.os.remove")
def test_clean_command_clean_build_dir(mock_os_remove, mock_shutil_rmtree):
    Path(BUILD_DIRECTORY).mkdir()
    clean_command()
    mock_os_remove.assert_not_called()
    mock_shutil_rmtree.assert_called_once_with(BUILD_DIRECTORY)
