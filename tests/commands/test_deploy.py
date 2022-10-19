"""Tests for deploy command."""
import logging
from unittest.mock import Mock, patch

import pytest

from nile.core.deploy import ABIS_DIRECTORY, BUILD_DIRECTORY, deploy
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class AsyncMock(Mock):
    """Return asynchronous mock."""

    async def __call__(self, *args, **kwargs):
        """Return mocked coroutine."""
        return super(AsyncMock, self).__call__(*args, **kwargs)


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
ABI = f"{ABIS_DIRECTORY}/{CONTRACT}.json"
ABI_OVERRIDE = f"{ABIS_DIRECTORY}/override.json"
BASE_PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
PATH_OVERRIDE = ("artifacts2", ABIS_DIRECTORY)
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222
RUN_OUTPUT = [ADDRESS, TX_HASH]


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
async def test_deploy(caplog, args, exp_abi):
    logging.getLogger().setLevel(logging.INFO)
    with patch("nile.core.deploy.capture_stdout", new=AsyncMock()) as mock_capture:
        mock_capture.return_value = RUN_OUTPUT
        with patch("nile.core.deploy.run_command", new=AsyncMock()):
            with patch("nile.core.deploy.parse_information") as mock_parse:
                mock_parse.return_value = RUN_OUTPUT
                with patch("nile.core.deploy.deployments.register") as mock_register:
                    # check return values
                    res = await deploy(*args)
                    assert res == (ADDRESS, exp_abi)

                    # check internals
                    mock_parse.assert_called_once_with(RUN_OUTPUT)
                    mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)

                    # check logs
                    assert f"🚀 Deploying {CONTRACT}" in caplog.text
                    assert (
                        f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
                        in caplog.text
                    )
                    assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
