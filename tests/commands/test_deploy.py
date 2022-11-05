"""Tests for deploy command."""
import logging
from unittest.mock import AsyncMock, patch

import pytest

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.core.deploy import deploy
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "localhost"
ALIAS = "alias"
ABI = f"{ABIS_DIRECTORY}/{CONTRACT}.json"
ABI_OVERRIDE = f"{ABIS_DIRECTORY}/override.json"
BASE_PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
PATH_OVERRIDE = ("artifacts2", ABIS_DIRECTORY)
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222
CALL_OUTPUT = [ADDRESS, TX_HASH]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_abi",
    [
        (
            [CONTRACT, ARGS, NETWORK, ALIAS],  # args
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE],  # args
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, None, ABI_OVERRIDE],  # args
            ABI_OVERRIDE,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE, ABI_OVERRIDE],  # args
            ABI_OVERRIDE,  # expected ABI
        ),
    ],
)
@patch("nile.core.deploy.parse_information", return_value=CALL_OUTPUT)
@patch("nile.core.deploy.deployments.register")
async def test_deploy(mock_register, mock_parse, caplog, args, exp_abi):
    logging.getLogger().setLevel(logging.INFO)

    with patch("nile.core.deploy.call_cli", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = CALL_OUTPUT

        # check return values
        res = await deploy(*args)
        assert res == (ADDRESS, exp_abi)

        # check internals
        mock_parse.assert_called_once_with(CALL_OUTPUT)
        mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)

        # check logs
        assert f"🚀 Deploying {CONTRACT}" in caplog.text
        assert (
            f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
