"""Tests for deploy command."""
import logging
from unittest.mock import patch

import pytest

from nile.core.deploy import ABIS_DIRECTORY, BUILD_DIRECTORY, deploy


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
ABI = f"{ABIS_DIRECTORY}/{CONTRACT}.json"
BASE_PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
PATH_OVERRIDE = ("artifacts2", ABIS_DIRECTORY)
RUN_OUTPUT = b"output"
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222


@pytest.mark.parametrize(
    "args, exp_command",
    [
        (
            [CONTRACT, ARGS, NETWORK, ALIAS],  # args
            [CONTRACT, NETWORK, None],  # expected command
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE],  # args
            [CONTRACT, NETWORK, PATH_OVERRIDE],  # expected command
        ),
    ],
)
@patch("nile.core.deploy.run_command", return_value=RUN_OUTPUT)
@patch("nile.core.deploy.parse_information", return_value=[ADDRESS, TX_HASH])
@patch("nile.core.deploy.deployments.register")
def test_deploy(mock_register, mock_parse, mock_run_cmd, caplog, args, exp_command):
    logging.getLogger().setLevel(logging.INFO)

    # check return values
    res = deploy(*args)
    assert res == (ADDRESS, ABI)

    # check internals
    mock_run_cmd.assert_called_once_with(*exp_command, arguments=ARGS)
    mock_parse.assert_called_once_with(RUN_OUTPUT)
    mock_register.assert_called_once_with(ADDRESS, ABI, NETWORK, ALIAS)

    # check logs
    assert f"🚀 Deploying {CONTRACT}" in caplog.text
    assert f"⏳ ️Deployment of {CONTRACT} successfully sent at {ADDRESS}" in caplog.text
    assert f"🧾 Transaction hash: {TX_HASH}" in caplog.text
