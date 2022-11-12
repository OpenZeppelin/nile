"""Tests for deploy command."""
import logging
from unittest.mock import patch

import pytest

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.core.deploy import deploy, deploy_account
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
CLASS_HASH = 1231
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222
SALT = 555
SIGNATURE = [111, 333]
FEE = 666
NONCE = 34
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
@patch("nile.core.deploy.capture_stdout", return_value=RUN_OUTPUT)
@patch("nile.core.deploy.parse_information", return_value=RUN_OUTPUT)
@patch("nile.core.deploy.deployments.register")
async def test_deploy(mock_register, mock_parse, mock_capture, caplog, args, exp_abi):
    logging.getLogger().setLevel(logging.INFO)

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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_abi",
    [
        (
            [
                NETWORK,
                SALT,
                ARGS,
                SIGNATURE,
                CONTRACT,
                FEE,
                NONCE,
                None,
                None,
                ALIAS,
            ],  # args
            ABI,  # expected ABI
        ),
        (
            [
                NETWORK,
                SALT,
                ARGS,
                SIGNATURE,
                CONTRACT,
                FEE,
                NONCE,
                None,
                PATH_OVERRIDE,
                ALIAS,
            ],  # args
            ABI,  # expected ABI
        ),
        (
            [
                NETWORK,
                SALT,
                ARGS,
                SIGNATURE,
                CONTRACT,
                FEE,
                NONCE,
                ABI_OVERRIDE,
                None,
                ALIAS,
            ],  # args
            ABI_OVERRIDE,  # expected ABI
        ),
        (
            [
                NETWORK,
                SALT,
                ARGS,
                SIGNATURE,
                CONTRACT,
                FEE,
                NONCE,
                ABI_OVERRIDE,
                PATH_OVERRIDE,
                ALIAS,
            ],  # args
            ABI_OVERRIDE,  # expected ABI
        ),
    ],
)
@patch("nile.core.deploy.deployments.register")
@patch(
    "nile.core.deploy.get_gateway_response",
    return_value={"address": ADDRESS, "tx_hash": TX_HASH},
)
@patch("nile.core.deploy.get_hash", return_value=CLASS_HASH)
async def test_deploy_account(
    mock_hash, mock_gateway, mock_register, caplog, args, exp_abi
):
    logging.getLogger().setLevel(logging.INFO)

    # check return values
    res = await deploy_account(*args)
    assert res == (ADDRESS, exp_abi)

    # check internals
    mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)

    # check logs
    assert f"🚀 Deploying {CONTRACT}" in caplog.text
    assert (
        f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
        in caplog.text
    )
    assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
