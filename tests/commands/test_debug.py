"""Tests for debug command."""
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from nile.common import BUILD_DIRECTORY
from nile.utils.debug import _abi_to_build_path, _locate_error_lines_with_abis, debug

MOCK_HASH = "0x1234"
NETWORK = "goerli"
ERROR_MESSAGE = "Error at pc=0:1:\nAn ASSERT_EQ instruction failed: 3 != 0."
DEBUG_ADDRESS = "0x07826b88e404632d9835ab1ec2076c6cf1910e6ecb2ed270647fc211ff55e76f"
ABI_PATH = "path/to/abis/test_contract.json"
ALIAS = "contract_alias"
MOCK_FILE = 123


def mocked_json_message(arg):
    return {"tx_status": arg, "tx_failure_reason": {"error_message": ERROR_MESSAGE}}


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test__abi_to_build_path():
    Path(BUILD_DIRECTORY).mkdir()
    filename = "contract"
    assert f"{BUILD_DIRECTORY}/{filename}" == _abi_to_build_path(filename)


@pytest.mark.parametrize(
    "file, address_set",
    [
        ([f"{DEBUG_ADDRESS}:{ABI_PATH}"], [int(DEBUG_ADDRESS, 16)]),
        ([f"{DEBUG_ADDRESS}:{ABI_PATH}:{ALIAS}"], [int(DEBUG_ADDRESS, 16)]),
    ],
)
@patch("nile.utils.debug._abi_to_build_path", return_value=ABI_PATH)
def test__locate_error_lines_with_abis_with_and_without_alias(
    mock_path, file, address_set
):
    with patch("nile.utils.debug.open") as mock_open:
        mock_open.return_value.__enter__.return_value = file
        return_array = _locate_error_lines_with_abis(MOCK_FILE, address_set, mock_path)
        # Values should be pushed into the array (and not return an error)
        # regardless if a contract alias is present or not
        assert return_array == [f"{DEBUG_ADDRESS}:{ABI_PATH}"]


@patch("nile.utils.debug._abi_to_build_path", return_value=ABI_PATH)
def test__locate_error_lines_with_abis_misformatted_line(mock_path, caplog):
    logging.getLogger().setLevel(logging.INFO)

    with patch("nile.utils.debug.open") as mock_open:
        # The DEBUG_ADDRESS alone without ":" is misformatted
        mock_open.return_value.__enter__.return_value = [DEBUG_ADDRESS]
        _locate_error_lines_with_abis(MOCK_FILE, int(DEBUG_ADDRESS, 16), mock_path)
        assert f"⚠ Skipping misformatted line #1 in {MOCK_FILE}" in caplog.text


@pytest.mark.parametrize(
    "args, expected",
    [
        ("ACCEPTED", "No error in transaction"),
        ("REJECTED", "The transaction was rejected"),
        ("REJECTED", ERROR_MESSAGE),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
@patch("nile.utils.debug.json.loads")
def test_debug_feedback_with_message(mock_json, caplog, args, expected):
    logging.getLogger().setLevel(logging.INFO)
    mock_json.return_value = mocked_json_message(args)

    debug(MOCK_HASH, NETWORK)

    assert expected in caplog.text
