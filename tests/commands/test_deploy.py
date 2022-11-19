"""Tests for deploy command."""
import logging
from unittest.mock import AsyncMock, patch

import pytest
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.core.account import Account
from nile.core.deploy import deploy, deploy_account, deploy_contract
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


EXP_SALTS = [
    2575391846029882800677169842619299590487820636126802982795520479739126412818,
    2557841322555501036413859939246042028937187876697248667793106475357514195630,
]
EXP_CLASS_HASHES = [
    0x434343,
    0x464646,
    0x494949,
    0x525252,
]
MOCK_ACC_ADDRESS = 0x123
MOCK_ACC_INDEX = 0
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
CALL_OUTPUT = [ADDRESS, TX_HASH]
SIGNATURE = [111, 333]
SALT = 555
FEE = 666


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, cmd_args, exp_abi",
    [
        (
            [CONTRACT, ARGS, NETWORK, ALIAS],  # args
            {
                "contract_name": CONTRACT,
                "inputs": ARGS,
                "overriding_path": None,
                "mainnet_token": None,
            },
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE],  # args
            {
                "contract_name": CONTRACT,
                "inputs": ARGS,
                "overriding_path": PATH_OVERRIDE,
                "mainnet_token": None,
            },
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, None, ABI_OVERRIDE],  # args
            {
                "contract_name": CONTRACT,
                "inputs": ARGS,
                "overriding_path": None,
                "mainnet_token": None,
            },
            ABI_OVERRIDE,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE, ABI_OVERRIDE],  # args
            {
                "contract_name": CONTRACT,
                "inputs": ARGS,
                "overriding_path": PATH_OVERRIDE,
                "mainnet_token": None,
            },
            ABI_OVERRIDE,  # expected ABI
        ),
    ],
)
@patch("nile.core.deploy.parse_information", return_value=CALL_OUTPUT)
@patch("nile.core.deploy.deployments.register")
async def test_deploy(mock_register, mock_parse, caplog, args, cmd_args, exp_abi):
    logging.getLogger().setLevel(logging.INFO)

    with patch("nile.core.deploy.execute_call", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = CALL_OUTPUT

        # check return values
        res = await deploy(*args)
        assert res == (ADDRESS, exp_abi)

        # check internals
        mock_parse.assert_called_once_with(CALL_OUTPUT)
        mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)
        mock_cli_call.assert_called_once_with("deploy", NETWORK, **cmd_args)

        # check logs
        assert f"🚀 Deploying {CONTRACT}" in caplog.text
        assert (
            f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_class_hash, exp_salt, exp_abi",
    [
        (
            [CONTRACT, 0, True, [], ALIAS, 0x424242, 5],  # args
            EXP_CLASS_HASHES[0],
            EXP_SALTS[0],
            ABI,
        ),
        (
            [CONTRACT, 1, False, [1], ALIAS, 0x454545, 0],  # args
            EXP_CLASS_HASHES[1],
            1,
            ABI,
        ),
        (
            [CONTRACT, 3, True, [1, 2], ALIAS, 0x484848, 0],  # args
            EXP_CLASS_HASHES[2],
            EXP_SALTS[1],
            ABI,
        ),
        (
            [
                CONTRACT,
                3,
                False,
                [1, 2, 3],
                ALIAS,
                0x515151,
                0,
                None,
                ABI_OVERRIDE,
            ],  # args
            EXP_CLASS_HASHES[3],
            3,
            ABI_OVERRIDE,
        ),
    ],
)
@patch(
    "nile.core.account.deploy_account", return_value=(MOCK_ACC_ADDRESS, MOCK_ACC_INDEX)
)
@patch("nile.core.account.Account.send", return_value=CALL_OUTPUT)
@patch("nile.core.deploy.parse_information", return_value=[ADDRESS, TX_HASH])
@patch("nile.core.deploy.deployments.register")
async def test_deploy_contract(
    mock_register,
    mock_parse,
    mock_send,
    mock_deploy,
    caplog,
    args,
    exp_class_hash,
    exp_salt,
    exp_abi,
):
    account = await Account("TEST_KEY", NETWORK)

    logging.getLogger().setLevel(logging.INFO)

    # decouple args
    (contract_name, salt, unique, calldata, alias, deployer_address, max_fee, *_) = args

    with patch("nile.core.deploy.get_class_hash") as mock_return_account:
        mock_return_account.return_value = exp_class_hash

        deployer_for_address_generation = deployer_address if unique else 0
        exp_address = calculate_contract_address_from_hash(
            exp_salt, exp_class_hash, calldata, deployer_for_address_generation
        )
        # check return values
        res = await deploy_contract(account, *args)
        assert res == (exp_address, exp_abi)

        # check internals
        mock_send.assert_called_once_with(
            deployer_address,
            method="deployContract",
            calldata=[exp_class_hash, salt, unique, len(calldata), *calldata],
            max_fee=max_fee,
        )
        mock_register.assert_called_once_with(exp_address, exp_abi, NETWORK, ALIAS)

        # check logs
        assert f"🚀 Deploying {CONTRACT}" in caplog.text
        assert (
            f"⏳ ️Deployment of {CONTRACT} successfully"
            + f" sent at {hex_address(exp_address)}"
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
    return_value={"address": ADDRESS, "transaction_hash": TX_HASH},
)
@patch("nile.core.deploy.get_account_class_hash", return_value=CLASS_HASH)
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
    assert f"🧾 Transaction hash: {TX_HASH}" in caplog.text
