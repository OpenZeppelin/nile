"""Tests for deploy command."""
import logging
from unittest.mock import patch

import pytest
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.core.account import Account
from nile.core.deploy import deploy, deploy_contract
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


MOCK_ACC_ADDRESS = 0x123
MOCK_ACC_INDEX = 0
CONTRACT = "contract"
NETWORK = "localhost"
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
            {  # expected command
                "contract_name": CONTRACT,
                "network": NETWORK,
                "overriding_path": None,
                "mainnet_token": None,
            },
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "network": NETWORK,
                "overriding_path": PATH_OVERRIDE,
                "mainnet_token": None,
            },
            ABI,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, None, ABI_OVERRIDE],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "network": NETWORK,
                "overriding_path": None,
                "mainnet_token": None,
            },
            ABI_OVERRIDE,  # expected ABI
        ),
        (
            [CONTRACT, ARGS, NETWORK, ALIAS, PATH_OVERRIDE, ABI_OVERRIDE],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "network": NETWORK,
                "overriding_path": PATH_OVERRIDE,
                "mainnet_token": None,
            },
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
    mock_run_cmd.assert_called_once_with(operation="deploy", inputs=ARGS, **exp_command)
    mock_parse.assert_called_once_with(RUN_OUTPUT)
    mock_register.assert_called_once_with(ADDRESS, exp_abi, NETWORK, ALIAS)

    # check logs
    assert f"🚀 Deploying {CONTRACT}" in caplog.text
    assert (
        f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
        in caplog.text
    )
    assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@pytest.mark.only
@pytest.mark.parametrize(
    "args, exp_class_hash, exp_salt, exp_abi",
    [
        (
            [CONTRACT, 0, True, [], ALIAS, 0x424242, 5],  # args
            0x434343,
            2575391846029882800677169842619299590487820636126802982795520479739126412818,
            ABI,
        ),
        (
            [CONTRACT, 1, False, [1], ALIAS, 0x454545, 0],  # args
            0x464646,
            1,
            ABI,
        ),
        (
            [CONTRACT, 3, True, [1, 2], ALIAS, 0x484848, 0],  # args
            0x494949,
            2557841322555501036413859939246042028937187876697248667793106475357514195630,
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
                "TEST_ABI",
            ],  # args
            0x525252,
            3,
            "TEST_ABI",
        ),
    ],
)
@patch("nile.core.account.deploy", return_value=(MOCK_ACC_ADDRESS, MOCK_ACC_INDEX))
@patch("nile.core.account.Account.send", return_value=RUN_OUTPUT)
@patch("nile.core.deploy.parse_information", return_value=[ADDRESS, TX_HASH])
@patch("nile.core.deploy.deployments.register")
def test_deploy_contract(
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
    account = Account("TEST_KEY", NETWORK)

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
        res = deploy_contract(account, *args)
        assert res == (exp_address, exp_abi)

        # check internals
        mock_send.assert_called_once_with(
            deployer_address,
            method="deployContract",
            calldata=[exp_class_hash, exp_salt, unique, len(calldata), *calldata],
            max_fee=max_fee,
        )
        mock_register.assert_called_once_with(exp_address, exp_abi, NETWORK, ALIAS)

        # check logs
        assert f"🚀 Deploying {CONTRACT}" in caplog.text
        assert (
            f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(exp_address)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
