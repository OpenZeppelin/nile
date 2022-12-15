"""Tests for account commands."""
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    QUERY_VERSION,
    TRANSACTION_VERSION,
    UNIVERSAL_DEPLOYER_ADDRESS,
)
from nile.core.types.account import Account
from nile.utils import normalize_number
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
DEPLOY_ACCOUNT_RESPONSE = (MOCK_ADDRESS, MOCK_TX_HASH, MOCK_ABI)


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.asyncio
@patch(
    "nile.core.types.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX)
)
async def test_account_init(mock_deploy):
    account = await Account(KEY, NETWORK)

    assert account.address == MOCK_ADDRESS
    assert account.index == MOCK_INDEX
    mock_deploy.assert_called_once()


@pytest.mark.asyncio
async def test_account_init_bad_key(caplog):
    logging.getLogger().setLevel(logging.INFO)

    await Account("BAD_KEY", NETWORK)
    assert (
        "\n❌ Cannot find BAD_KEY in env."
        "\nCheck spelling and that it exists."
        "\nTry moving the .env to the root of your project."
    ) in caplog.text


@pytest.mark.asyncio
@patch(
    "nile.core.types.account.deploy_account",
    return_value=DEPLOY_ACCOUNT_RESPONSE,
)
@patch("nile.common.get_class_hash", return_value=CLASS_HASH)
@patch("nile.core.types.account.Signer.sign", return_value=SIGNATURE)
@patch("nile.core.types.account.os.path.dirname")
async def test_deploy(mock_path, mock_signer, mock_hash, mock_deploy):
    test_path = "/overriding_path"
    overriding_path = (
        f"{test_path}/artifacts",
        f"{test_path}/artifacts/abis",
    )

    mock_path.return_value.replace.return_value = test_path

    account = await Account(KEY, NETWORK, salt=SALT, max_fee=MAX_FEE)
    calldata = [account.signer.public_key]

    mock_deploy.assert_called_with(
        network=NETWORK,
        salt=SALT,
        calldata=calldata,
        signature=SIGNATURE,
        max_fee=MAX_FEE,
        query_type=None,
        overriding_path=overriding_path,
        watch_mode=None,
    )


@pytest.mark.asyncio
@patch(
    "nile.core.types.account.deploy_account",
    return_value=DEPLOY_ACCOUNT_RESPONSE,
)
@patch("nile.core.types.account.get_account_class_hash", return_value=CLASS_HASH)
@patch("nile.core.types.account.accounts.register")
async def test_deploy_accounts_register(mock_register, mock_hash, mock_deploy):
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
    mock_process_arguments, mock_get_class, contract_name, max_fee, nonce, alias, overriding_path
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
        assert tx_wrapper.overriding_path == overriding_path

        # Check transaction
        tx = tx_wrapper.tx
        assert tx.tx_type == 'declare'
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
            alias,
            max_fee,
            nonce=nonce,
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
@pytest.mark.parametrize("calldata", [[1,2,3]])
@pytest.mark.parametrize("max_fee", [0, None])
@pytest.mark.parametrize("nonce", [0])
@patch("nile.core.types.account.Account._process_arguments")
async def test_send(
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
        assert tx.tx_type == 'invoke'
        assert tx.entry_point == '__execute__'
        assert tx.account_address == account.address
        assert tx.max_fee == (max_fee or 0)
        assert tx.nonce == nonce
        assert tx.network == account.network
        assert tx.version == TRANSACTION_VERSION

        # Check '_process_arguments' call
        mock_process_arguments.assert_called_once_with(max_fee, nonce, calldata)
