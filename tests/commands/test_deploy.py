"""Tests for deploy command."""
import logging
from unittest.mock import AsyncMock, patch

import pytest

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.core.deploy import deploy, deploy_account, deploy_contract
from nile.core.types.transactions import DeployAccountTransaction
from nile.core.types.udc_helpers import create_udc_deploy_transaction
from nile.utils import hex_address
from nile.utils.status import TransactionStatus, TxStatus
from tests.mocks.mock_account import MockAccount


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
CLASS_HASH = 1231
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222
CALL_OUTPUT = [ADDRESS, TX_HASH]
SIGNATURE = [111, 333]
SALT = 555
FEE = 666
TX_STATUS = TransactionStatus(TX_HASH, TxStatus.ACCEPTED_ON_L2, None)


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
@pytest.mark.parametrize("contract_name", [CONTRACT])
@pytest.mark.parametrize("alias", ["my_contract", None])
@pytest.mark.parametrize("predicted_address", [0x123, 0x456])
@pytest.mark.parametrize("abi", ["TEST_EXPECTED_ABI"])
@pytest.mark.parametrize("overriding_path", [PATH_OVERRIDE, None])
@pytest.mark.parametrize("watch_mode", ["track", None])
@patch(
    "nile.core.types.transactions.Transaction.execute", return_value=(TX_STATUS, None)
)
@patch("nile.core.deploy.parse_information", return_value=[ADDRESS, TX_HASH])
@patch("nile.core.deploy.deployments.register")
async def test_deploy_contract(
    mock_register,
    mock_parse,
    mock_execute,
    caplog,
    contract_name,
    alias,
    predicted_address,
    abi,
    overriding_path,
    watch_mode,
):

    logging.getLogger().setLevel(logging.INFO)

    account = await MockAccount("TEST_KEY", NETWORK)
    with patch("nile.core.types.udc_helpers.get_class_hash") as mock_get_class_hash:
        mock_get_class_hash.return_value = 0x777

        transaction, _ = await create_udc_deploy_transaction(
            account=account,
            contract_name=contract_name,
            salt=0,
            unique=False,
            calldata=[],
            deployer_address=0x456,
            max_fee=0,
            nonce=0,
        )

        register_abi = abi
        if abi is None:
            register_abi = ABI

        # check return values
        res = await deploy_contract(
            transaction,
            account.signer,
            contract_name,
            alias,
            predicted_address,
            abi=abi,
            overriding_path=overriding_path,
            watch_mode=watch_mode,
        )
        assert res == (TX_STATUS, predicted_address, register_abi)

        # check internals
        mock_execute.assert_called_once_with(
            signer=account.signer, watch_mode=watch_mode
        )
        mock_register.assert_called_once_with(
            predicted_address, register_abi, NETWORK, alias
        )

        # check logs
        assert f"🚀 Deploying {contract_name}" in caplog.text
        assert (
            f"⏳ ️Deployment of {contract_name} successfully"
            + f" sent at {hex_address(predicted_address)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("contract_name", [CONTRACT])
@pytest.mark.parametrize("alias", [ALIAS])
@pytest.mark.parametrize("predicted_address", [ADDRESS])
@pytest.mark.parametrize("overriding_path", [None, PATH_OVERRIDE])
@pytest.mark.parametrize("abi", [None, ABI_OVERRIDE])
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch(
    "nile.core.types.transactions.Transaction.execute",
    return_value=(TX_STATUS, "output"),
)
@patch("nile.core.types.transactions.get_class_hash", return_value=CLASS_HASH)
@patch("nile.core.deploy.deployments.register")
@patch("nile.core.deploy.accounts.register")
@patch("nile.accounts.current_index", return_value=MOCK_ACC_INDEX)
async def test_deploy_account(
    mock_index,
    mock_accounts_register,
    mock_deployments_register,
    mock_get_class_hash,
    mock_execute,
    caplog,
    contract_name,
    alias,
    predicted_address,
    overriding_path,
    abi,
    watch_mode,
):
    logging.getLogger().setLevel(logging.INFO)

    account = await MockAccount("TEST_KEY", NETWORK)
    exp_abi = ABI if abi is None else abi

    with patch(
        "nile.core.types.transactions.DeployAccountTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = 0x777

        transaction = DeployAccountTransaction()

        # check return values
        res = await deploy_account(
            transaction=transaction,
            signer=account.signer,
            contract_name=contract_name,
            alias=alias,
            predicted_address=predicted_address,
            overriding_path=overriding_path,
            abi=abi,
            watch_mode=watch_mode,
        )
        assert res == (TX_STATUS, ADDRESS, exp_abi)

        # check internals
        mock_deployments_register.assert_called_once_with(
            ADDRESS, exp_abi, NETWORK, ALIAS
        )
        mock_accounts_register.assert_called_once_with(
            account.signer.public_key, ADDRESS, MOCK_ACC_INDEX, ALIAS, NETWORK
        )
        mock_execute.assert_called_once_with(
            signer=account.signer, watch_mode=watch_mode
        )

        # check logs
        assert f"🚀 Deploying {CONTRACT}" in caplog.text
        assert (
            f"⏳ ️Deployment of {CONTRACT} successfully sent at {hex_address(ADDRESS)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text
