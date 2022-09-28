"""Tests for deploy command."""
import logging
from unittest.mock import patch

import pytest

from nile.core.deploy import ABIS_DIRECTORY, BUILD_DIRECTORY, deploy
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
ABI = f"{ABIS_DIRECTORY}/{CONTRACT}.json"
ABI_OVERRIDE = f"{ABIS_DIRECTORY}/override.json"
BASE_PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
PATH_OVERRIDE = ("artifacts2", ABIS_DIRECTORY)
RUN_OUTPUT = b"output"
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222


@pytest.mark.parametrize(
    "args, exp_command, exp_abi",
    [
        (
            [CONTRACT, ARGS, NETWORK, ALIAS],  # args
            [CONTRACT, NETWORK, None],  # expected command
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE],  # args
            [CONTRACT, NETWORK, PATH_OVERRIDE],  # expected command
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, None, ABI_OVERRIDE],  # args
            [CONTRACT, NETWORK, None],  # expected command
            ABI_OVERRIDE,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE, ABI_OVERRIDE],  # args
            [CONTRACT, NETWORK, PATH_OVERRIDE],  # expected command
            ABI_OVERRIDE,  # expected ABI
        ),
    ],
)
@patch("nile.core.deploy.run_command", return_value=RUN_OUTPUT)
@patch("nile.core.deploy.parse_information", return_value=[ADDRESS, TX_HASH])
@patch("nile.core.deploy.deployments.register")
def test_deploy(
    mock_register, mock_parse, mock_run_cmd, caplog, args, exp_command, exp_abi
):
    logging.getLogger().setLevel(logging.INFO)

    # check return values
    res = deploy(*args)
    assert res == (ADDRESS, exp_abi)

    # check internals
    mock_run_cmd.assert_called_once_with(*exp_command, arguments=ARGS)
    mock_parse.assert_called_once_with(RUN_OUTPUT)
    mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)

    # check logs
    assert f"🚀 Deploying {CONTRACT}" in caplog.text
    assert (
        f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
        in caplog.text
    )
    assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
