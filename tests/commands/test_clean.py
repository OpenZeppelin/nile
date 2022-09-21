"""Tests for clean command."""
from pathlib import Path
from unittest.mock import patch

import pytest

from nile.core.commands.clean import clean
from nile.core.common import (
    ACCOUNTS_FILENAME,
    BUILD_DIRECTORY,
    DECLARATIONS_FILENAME,
    DEPLOYMENTS_FILENAME,
)


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@patch("nile.core.commands.clean.shutil.rmtree")
@patch("nile.core.commands.clean.os.remove")
def test_clean_already_clean(mock_os_remove, mock_shutil_rmtree):
    clean()
    mock_os_remove.assert_not_called()
    mock_shutil_rmtree.assert_not_called()


@pytest.mark.parametrize(
    "fname",
    [
        f"localhost.{ACCOUNTS_FILENAME}",
        f"localhost.{DEPLOYMENTS_FILENAME}",
        f"localhost.{DECLARATIONS_FILENAME}",
    ],
)
@patch("nile.core.commands.clean.shutil.rmtree")
@patch("nile.core.commands.clean.os.remove")
def test_clean_clean_files(mock_os_remove, mock_shutil_rmtree, fname):
    Path(fname).touch()
    clean()
    mock_os_remove.assert_called_once_with(fname)
    mock_shutil_rmtree.assert_not_called()


@patch("nile.core.commands.clean.shutil.rmtree")
@patch("nile.core.commands.clean.os.remove")
def test_clean_clean_build_dir(mock_os_remove, mock_shutil_rmtree):
    Path(BUILD_DIRECTORY).mkdir()
    clean()
    mock_os_remove.assert_not_called()
    mock_shutil_rmtree.assert_called_once_with(BUILD_DIRECTORY)
