"""Tests for get-nonce command."""
import logging
from unittest.mock import AsyncMock, patch

import pytest

from nile.utils.get_nonce import get_nonce, get_nonce_without_log

NONCE = 5
NETWORK = "localhost"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "contract_address, network",
    [("0xffff", "localhost"), ("0xffff", "goerli"), ("0xffff", "mainnet")],
)
async def test_get_nonce(contract_address, network, caplog):
    logging.getLogger().setLevel(logging.INFO)

    with patch("nile.utils.get_nonce.execute_call", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = NONCE
        nonce = await get_nonce(contract_address, network)
        assert nonce == NONCE

        command_args = {"contract_address": contract_address}
        mock_cli_call.assert_called_once_with("get_nonce", network, **command_args)

        # Check log
        assert f"Current Nonce: {NONCE}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "contract_address",
    ["0x4d2", "1234", 1234],
)
async def test_get_nonce_without_log_address_formats(contract_address):
    with patch("nile.utils.get_nonce.execute_call", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = NONCE
        await get_nonce_without_log(contract_address, NETWORK)

        command_args = {"contract_address": "0x4d2"}
        mock_cli_call.assert_called_once_with("get_nonce", NETWORK, **command_args)
