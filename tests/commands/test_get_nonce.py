"""Tests for get-nonce command."""
import logging
from unittest.mock import patch, AsyncMock

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
async def test_get_nonce_without_log_address_formats(contract_address):
    with patch("nile.utils.get_nonce.call_cli", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = NONCE
        await get_nonce_without_log(contract_address, "goerli")

        args = set_args("goerli")
        command_args = ["--contract_address", "0x4d2"]
        mock_cli_call.assert_called_once_with("get_nonce", args, command_args)
