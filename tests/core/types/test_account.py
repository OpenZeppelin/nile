"""Tests for account commands."""

from unittest.mock import patch

import pytest

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    NILE_ARTIFACTS_PATH,
    TRANSACTION_VERSION,
    UNIVERSAL_DEPLOYER_ADDRESS,
)
from nile.core.types.account import Account
from nile.core.types.tx_wrappers import DeployAccountTxWrapper
from nile.utils import normalize_number
from nile.utils.status import TransactionStatus, TxStatus
from tests.mocks.mock_account import MockAccount

KEY = "TEST_KEY"
NETWORK = "localhost"
MOCK_ADDRESS = 0x123
MOCK_TARGET_ADDRESS = 0x987
MOCK_INDEX = 0
MOCK_ABI = "MOCK_ABI"
MOCK_TX_HASH = 1
MAX_FEE = 10
SALT = 444
SIGNATURE = [111, 222]
CLASS_HASH = 12345
PATH = ("src/nile/artifacts", "src/nile/artifacts/abis")
TX_STATUS = TransactionStatus(MOCK_TX_HASH, TxStatus.ACCEPTED_ON_L2, None)
DEPLOY_ACCOUNT_RESPONSE = (TX_STATUS, MOCK_ADDRESS, MOCK_ABI)
MOCK_DEPLOY_ACC_TX_WRAPPER = DeployAccountTxWrapper(None, None)


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.asyncio
async def test_account_init_bad_key():
    with pytest.raises(KeyError):
        await Account("BAD_KEY", NETWORK)


@pytest.mark.asyncio
@pytest.mark.parametrize("salt", [0, 1])
@pytest.mark.parametrize("max_fee", [0, 15, None])
@pytest.mark.parametrize("abi", [None, "TEST_ABI"])
@patch("nile.core.types.transactions.get_class_hash", return_value=CLASS_HASH)
@patch("nile.core.types.account.get_counterfactual_address", return_value=MOCK_ADDRESS)
@patch("nile.core.types.account.Account._process_arguments")
async def test_deploy(
    mock_process_arguments,
    mock_address,
    mock_class_hash,
    salt,
    max_fee,
    abi,
):
    account = await MockAccount(KEY, NETWORK)
    calldata = [account.signer.public_key]
    mock_process_arguments.return_value = ((max_fee or 0), 0, calldata)

    with patch(
        "nile.core.types.transactions.DeployAccountTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = 0x777

        tx_wrapper = await account.deploy(
            salt=salt,
            max_fee=max_fee,
            abi=abi,
        )

        # Check transaction wrapper
        assert tx_wrapper.account == account
        assert tx_wrapper.alias == account.alias
        assert tx_wrapper.abi == abi

        # Check transaction
        tx = tx_wrapper.tx
        assert tx.tx_type == "deploy_account"
        assert tx.account_address == 0
        assert tx.contract_to_submit == "Account"
        assert tx.predicted_address == MOCK_ADDRESS
        assert tx.calldata == calldata
        assert tx.class_hash == CLASS_HASH
        assert tx.overriding_path == NILE_ARTIFACTS_PATH
        assert tx.max_fee == (max_fee or 0)
        assert tx.nonce == 0
        assert tx.network == account.network
        assert tx.version == TRANSACTION_VERSION

        # Check internals
        mock_class_hash.assert_called_once_with(
            contract_name="Account", overriding_path=NILE_ARTIFACTS_PATH
        )

        # Check '_process_arguments' call
        mock_process_arguments.assert_called_once_with(max_fee, 0, calldata)


@pytest.mark.asyncio
@patch(
    "nile.core.types.transactions.Transaction.execute",
    return_value=(TX_STATUS, "output"),
)
@patch("nile.core.types.account.get_counterfactual_address", return_value=MOCK_ADDRESS)
@patch("nile.core.types.transactions.get_class_hash", return_value=CLASS_HASH)
@patch("nile.core.deploy.accounts.register")
@patch("nile.core.types.account._set_estimated_fee_if_none")
async def test_deploy_accounts_register(
    mock_set_fee, mock_register, mock_hash, mock_address, mock_deploy
):
    account = await Account(KEY, NETWORK)

    mock_register.assert_called_once_with(
        account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, KEY, NETWORK
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("contract_name", ["contract"])
@pytest.mark.parametrize("max_fee", [0, 15, None])
@pytest.mark.parametrize("nonce", [0])
@pytest.mark.parametrize("alias", ["my_contract"])
@pytest.mark.parametrize("overriding_path", [(BUILD_DIRECTORY, ABIS_DIRECTORY), None])
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.account.Account._process_arguments")
async def test_declare(
    mock_process_arguments,
    mock_get_class,
    contract_name,
    max_fee,
    nonce,
    alias,
    overriding_path,
):
    account = await MockAccount(KEY, NETWORK)
    mock_process_arguments.return_value = ((max_fee or 0), nonce, None)

    with patch(
        "nile.core.types.transactions.DeclareTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = 0x777

        tx_wrapper = await account.declare(
            contract_name,
            max_fee=max_fee,
            nonce=nonce,
            alias=alias,
            overriding_path=overriding_path,
        )

        # Check transaction wrapper
        assert tx_wrapper.account == account
        assert tx_wrapper.alias == alias

        # Check transaction
        tx = tx_wrapper.tx
        assert tx.tx_type == "declare"
        assert tx.account_address == account.address
        assert tx.contract_to_submit == contract_name
        assert tx.contract_class == "ContractClass"
        assert tx.overriding_path == overriding_path
        assert tx.max_fee == (max_fee or 0)
        assert tx.nonce == nonce
        assert tx.network == account.network
        assert tx.version == TRANSACTION_VERSION

        # Check internals
        mock_get_class.assert_called_once_with(
            contract_name=contract_name, overriding_path=overriding_path
        )

        # Check '_process_arguments' call
        mock_process_arguments.assert_called_once_with(max_fee, nonce)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "nile_account, overriding_path", [(False, None), (True, NILE_ARTIFACTS_PATH)]
)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.account.DeclareTransaction", return_value="tx")
@patch("nile.core.types.account.DeclareTxWrapper")
@patch("nile.core.types.account._set_estimated_fee_if_none")
async def test_declare_account(
    mock_set_fee,
    mock_tx_wrapper,
    mock_tx,
    mock_contract_class,
    nile_account,
    overriding_path,
):
    # mock_tx_wrapper = AsyncMock()
    account = await MockAccount(KEY, NETWORK)

    contract_name = "Account"

    await account.declare(contract_name, nonce=0, nile_account=nile_account)

    # Check 'DeclareTransaction' call
    mock_tx.assert_called_once_with(
        account_address=account.address,
        contract_to_submit=contract_name,
        max_fee=0,
        nonce=0,
        network=account.network,
        overriding_path=overriding_path,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("contract_name", ["contract"])
@pytest.mark.parametrize("salt", [0])
@pytest.mark.parametrize("unique", [True, False])
@pytest.mark.parametrize("calldata", [[0x123, 456]])
@pytest.mark.parametrize("alias", ["my_contract"])
@pytest.mark.parametrize("max_fee", [10, None])
@pytest.mark.parametrize("nonce", [0])
@pytest.mark.parametrize("deployer_address", [None, 0xDE0])
@pytest.mark.parametrize("overriding_path", [None, PATH])
@pytest.mark.parametrize("abi", [None, "TEST_ABI"])
@patch("nile.core.types.account.Account._process_arguments")
async def test_deploy_contract(
    mock_process_arguments,
    contract_name,
    salt,
    unique,
    calldata,
    alias,
    max_fee,
    nonce,
    deployer_address,
    overriding_path,
    abi,
):
    account = await MockAccount(KEY, NETWORK)
    mock_process_arguments.return_value = ((max_fee or 0), nonce, calldata)

    transaction = "transaction_mock"
    predicted_address = 0x876
    with patch(
        "nile.core.types.account.create_udc_deploy_transaction"
    ) as mock_udc_transaction:
        mock_udc_transaction.return_value = transaction, predicted_address

        tx_wrapper = await account.deploy_contract(
            contract_name,
            salt,
            unique,
            calldata,
            nonce=nonce,
            max_fee=max_fee,
            alias=alias,
            deployer_address=deployer_address,
            overriding_path=overriding_path,
            abi=abi,
        )

        # Check transaction wrapper
        assert tx_wrapper.tx == transaction
        assert tx_wrapper.account == account
        assert tx_wrapper.alias == alias
        assert tx_wrapper.overriding_path == overriding_path
        assert tx_wrapper.predicted_address == predicted_address
        assert tx_wrapper.abi == abi

        # Check internals
        mock_udc_transaction.assert_called_once_with(
            account=account,
            contract_name=contract_name,
            salt=salt,
            unique=unique,
            calldata=calldata,
            deployer_address=(
                deployer_address or normalize_number(UNIVERSAL_DEPLOYER_ADDRESS)
            ),
            max_fee=(max_fee or 0),
            nonce=nonce,
            overriding_path=overriding_path,
        )

        # Check '_process_arguments' call
        mock_process_arguments.assert_called_once_with(max_fee, nonce, calldata)


@pytest.mark.asyncio
@pytest.mark.parametrize("address_or_alias", ["my_contract", 0x123, "0x123"])
@pytest.mark.parametrize("method", ["method"])
@pytest.mark.parametrize("calldata", [[1, 2, 3]])
@pytest.mark.parametrize("max_fee", [0, None])
@pytest.mark.parametrize("nonce", [0])
@patch("nile.core.types.account.Account._process_arguments")
@patch("nile.core.types.account.deployments.load")
async def test_send(
    mock_load,
    mock_process_arguments,
    address_or_alias,
    method,
    calldata,
    max_fee,
    nonce,
):
    account = await MockAccount(KEY, NETWORK)
    mock_process_arguments.return_value = ((max_fee or 0), nonce, calldata)

    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = 0x777
        mock_load.return_value = iter([(0x123, 0)])

        tx_wrapper = await account.send(
            address_or_alias=address_or_alias,
            method=method,
            calldata=calldata,
            nonce=nonce,
            max_fee=max_fee,
        )

        # Check transaction wrapper
        assert tx_wrapper.account == account

        # Check transaction
        tx = tx_wrapper.tx
        assert tx.tx_type == "invoke"
        assert tx.entry_point == "__execute__"
        assert tx.account_address == account.address
        assert tx.max_fee == (max_fee or 0)
        assert tx.nonce == nonce
        assert tx.network == account.network
        assert tx.version == TRANSACTION_VERSION

        # Check '_process_arguments' call
        mock_process_arguments.assert_called_once_with(max_fee, nonce, calldata)
