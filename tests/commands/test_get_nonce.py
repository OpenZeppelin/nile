"""Tests for get-nonce command."""
import logging
from unittest.mock import patch

import pytest

from nile.common import set_args
from nile.utils.get_nonce import get_nonce, get_nonce_without_log

NONCE = 5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "contract_address, network",
    [("0xffff", "localhost"), ("0xffff", "goerli"), ("0xffff", "mainnet")],
)
@patch("nile.utils.get_nonce.get_nonce_without_log")
async def test_get_nonce(mock_without_log, contract_address, network, caplog):
    logging.getLogger().setLevel(logging.INFO)

    mock_without_log.return_value = NONCE

    # Check return value
    nonce = await get_nonce(contract_address, network)
    assert nonce == NONCE

    # Check internal
    mock_without_log.assert_called_once_with(contract_address, network)

    # Check log
    assert f"Current Nonce: {NONCE}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "contract_address",
    ["0x4d2", "1234", 1234],
)
@patch("nile.utils.get_nonce.starknet_cli.get_nonce")
@patch("nile.utils.get_nonce.capture_stdout", return_value=NONCE)
async def test_get_nonce_without_log_address_formats(
    mock_capture, mock_sn_get_nonce, contract_address
):
    await get_nonce_without_log(contract_address, "goerli")

    args = set_args("goerli")
    command = ["--contract_address", "0x4d2"]
    mock_sn_get_nonce.assert_called_once_with(args=args, command_args=command)
