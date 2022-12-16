"""Tests for debug command."""
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from nile.common import BUILD_DIRECTORY, DEPLOYMENTS_FILENAME
from nile.utils.debug import (
    _abi_to_path,
    _get_contracts_data,
    _locate_error_lines_with_abis,
)
from nile.utils.status import status

MOCK_HASH = 1234
NETWORK = "localhost"
DEBUG_ADDRESS = "0x07826b88e404632d9835ab1ec2076c6cf1910e6ecb2ed270647fc211ff55e76f"
ABI_PATH = "path/to/abis/test_contract.json"
ALIAS = "contract_alias"
MOCK_FILE = 123
ACCEPTED_OUT = b'{"tx_status": "ACCEPTED_ON_L2"}'
REJECTED_OUT = b'{"tx_failure_reason": {"error_message": "E"}, "tx_status": "REJECTED"}'
ADDRESSES = {0x123, 0x456}


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test__abi_to_path():
    Path(BUILD_DIRECTORY).mkdir()
    open(f"{BUILD_DIRECTORY}/contract.json", "w")

    assert f"{BUILD_DIRECTORY}/contract.json" == _abi_to_path("contract.json")


@pytest.mark.parametrize(
    "file, address_set",
    [
        ([f"{DEBUG_ADDRESS}:{ABI_PATH}"], [int(DEBUG_ADDRESS, 16)]),
        ([f"{DEBUG_ADDRESS}:{ABI_PATH}:{ALIAS}"], [int(DEBUG_ADDRESS, 16)]),
    ],
)
@patch("nile.utils.debug._abi_to_path", return_value=ABI_PATH)
def test__locate_error_lines_with_abis_with_and_without_alias(
    mock_path, file, address_set
):
    with patch("nile.utils.debug.open") as mock_open, patch(
        "os.path.isfile", return_value=True
    ):
        mock_open.return_value.__enter__.return_value = file
        return_array = _locate_error_lines_with_abis(MOCK_FILE, address_set, mock_path)
        # Values should be pushed into the array (and not return an error)
        # regardless if a contract alias is present or not
        assert return_array == [f"{DEBUG_ADDRESS}:{ABI_PATH}"]


@patch("nile.utils.debug._abi_to_path", return_value=ABI_PATH)
def test__locate_error_lines_with_abis_misformatted_line(mock_path, caplog):
    logging.getLogger().setLevel(logging.INFO)

    with patch("nile.utils.debug.open") as mock_open, patch(
        "os.path.isfile", return_value=True
    ):
        # The DEBUG_ADDRESS alone without ":" is misformatted
        mock_open.return_value.__enter__.return_value = [DEBUG_ADDRESS]
        _locate_error_lines_with_abis(MOCK_FILE, int(DEBUG_ADDRESS, 16), mock_path)
        assert f"⚠ Skipping misformatted line #1 in {MOCK_FILE}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "output, expected",
    [
        (ACCEPTED_OUT, "No error in transaction"),
        (REJECTED_OUT, "The transaction was rejected"),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
@patch("nile.utils.status.execute_call")
async def test_status_feedback_with_message(mock_output, output, expected, caplog):
    logging.getLogger().setLevel(logging.INFO)
    mock_output.return_value = output

    await status(MOCK_HASH, NETWORK, "debug")

    assert expected in caplog.text


@pytest.mark.parametrize(
    "contracts_file, expected",
    [
        (None, _abi_to_path),
        ("contracts_file.json", "contracts_file.json"),
    ],
)
@patch("nile.utils.debug._locate_error_lines_with_abis")
def test__get_contracts_data(mock_locate, contracts_file, expected):
    _get_contracts_data(contracts_file, NETWORK, ADDRESSES)

    if not contracts_file:
        mock_locate.assert_called_once_with(
            f"{NETWORK}.{DEPLOYMENTS_FILENAME}", ADDRESSES, expected
        )
    else:
        _contracts_file = mock_locate.call_args[0][0]
        assert _contracts_file == expected
