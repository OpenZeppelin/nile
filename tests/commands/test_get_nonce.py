"""Tests for get-nonce command."""
import logging
from unittest.mock import Mock, patch

import pytest

from nile.common import Args, get_feeder_url
from nile.utils.get_nonce import get_nonce, get_nonce_without_log

NONCE = 5


class AsyncMock(Mock):
    """Return asynchronous mock."""

    async def __call__(self, *args, **kwargs):
        """Return mocked coroutine."""
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "contract_address, network",
    [("0xffff", "localhost"), ("0xffff", "goerli"), ("0xffff", "mainnet")],
)
async def test_get_nonce(contract_address, network, caplog):
    logging.getLogger().setLevel(logging.INFO)
    with patch(
        "nile.utils.get_nonce.get_nonce_without_log", new=AsyncMock()
    ) as mock_without_log:
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
    with patch(
        "nile.utils.get_nonce.starknet_cli.get_nonce", new=AsyncMock()
    ) as mock_starknet_cli:
        await get_nonce_without_log(contract_address, "goerli")

        args = Args()
        args.feeder_gateway_url = get_feeder_url("goerli")

        command = ["--contract_address", "0x4d2"]

        mock_starknet_cli.assert_called_once_with(args=args, command_args=command)
