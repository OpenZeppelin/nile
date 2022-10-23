"""Tests for account commands."""
import logging
from unittest.mock import ANY, MagicMock, patch

import pytest

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    QUERY_VERSION,
    TRANSACTION_VERSION,
)
from nile.core.account import Account

KEY = "TEST_KEY"
NETWORK = "goerli"
MOCK_ADDRESS = "0x123"
MOCK_INDEX = 0
MAX_FEE = 10


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@patch("nile.core.account.Account.deploy")
def test_account_init(mock_deploy):
    mock_deploy.return_value = MOCK_ADDRESS, MOCK_INDEX
    account = Account(KEY, NETWORK)

    assert account.address == MOCK_ADDRESS
    assert account.index == MOCK_INDEX
    mock_deploy.assert_called_once()


def test_account_init_bad_key(caplog):
    logging.getLogger().setLevel(logging.INFO)

    Account("BAD_KEY", NETWORK)
    assert (
        "\n❌ Cannot find BAD_KEY in env."
        "\nCheck spelling and that it exists."
        "\nTry moving the .env to the root of your project."
    ) in caplog.text


@patch("nile.core.account.deploy", return_value=(1, 2))
def test_deploy(mock_deploy):
    account = Account(KEY, NETWORK)
    with patch("nile.core.account.os.path.dirname") as mock_path:
        test_path = "/overriding_path"
        mock_path.return_value.replace.return_value = test_path

        mock_deploy.assert_called_with(
            "Account",
            [account.signer.public_key],
            NETWORK,
            f"account-{account.index}",
            ANY,
        )


@patch("nile.core.account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.accounts.register")
def test_deploy_accounts_register(mock_register, mock_deploy):
    account = Account(KEY, NETWORK)

    mock_register.assert_called_once_with(
        account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, KEY, NETWORK
    )


@patch("nile.core.account.get_contract_class", return_value="ContractClass")
@patch("nile.core.account.declare")
def test_declare(mock_declare, mock_get_class):
    account = Account(KEY, NETWORK)
    signature = [999, 888]
    nonce = 4
    max_fee = 1
    contract_name = "contract"
    alias = "my_contract"
    overriding_path = (BUILD_DIRECTORY, ABIS_DIRECTORY)

    account.signer.sign_declare = MagicMock(return_value=signature)

    account.declare(
        contract_name,
        max_fee=max_fee,
        nonce=nonce,
        alias=alias,
        overriding_path=overriding_path,
    )

    # Check 'get_contract_class' call
    mock_get_class.assert_called_once_with(
        contract_name=contract_name, overriding_path=overriding_path
    )

    # Check values are correctly passed to 'sign_declare'
    account.signer.sign_declare.assert_called_once_with(
        sender=account.address,
        contract_class="ContractClass",
        nonce=nonce,
        max_fee=max_fee,
    )

    # Check values are correctly passed to 'core.declare'
    mock_declare.assert_called_with(
        sender=account.address,
        contract_name=contract_name,
        signature=signature,
        network=NETWORK,
        alias=alias,
        max_fee=max_fee,
    )


@patch("nile.core.account.get_nonce", return_value=0)
@patch("nile.core.account.call_or_invoke")
def test_send_nonce_call(mock_call, mock_nonce):
    account = Account(KEY, NETWORK)

    # Instead of creating and populating a tmp .txt file, this uses the
    # deployed account address (contract_address) as the target
    account.send(account.address, "method", [1, 2, 3], max_fee=1)

    # 'call_or_invoke' is called once for '__execute__'
    assert mock_call.call_count == 1

    # Check 'get_nonce' call
    mock_nonce.assert_called_once_with(account.address, NETWORK)


def test_send_sign_transaction_and_execute():
    account = Account(KEY, NETWORK)

    calldata = ["111", "222", "333"]
    sig_r, sig_s = [999, 888]
    return_signature = [calldata, sig_r, sig_s]

    account.signer.sign_transaction = MagicMock(return_value=return_signature)

    with patch("nile.core.account.call_or_invoke") as mock_call:
        send_args = [account.address, "method", [1, 2, 3]]
        nonce = 4
        max_fee = 1
        account.send(*send_args, max_fee, nonce)

        # Check values are correctly passed to 'sign_transaction'
        account.signer.sign_transaction.assert_called_once_with(
            calls=[send_args],
            nonce=nonce,
            sender=account.address,
            max_fee=1,
            version=TRANSACTION_VERSION,
        )

        # Check values are correctly passed to '__execute__'
        mock_call.assert_called_with(
            contract=account,
            max_fee=str(max_fee),
            method="__execute__",
            network=NETWORK,
            params=calldata,
            signature=[str(sig_r), str(sig_s)],
            type="invoke",
            query_flag=None,
        )


def test_estimate_fee():
    account = Account(KEY, NETWORK)
    # Mock send
    account.send = MagicMock()

    account.estimate_fee(account.address, "method", [1, 2, 3], max_fee=0)

    account.send.assert_called_once_with(
        account.address, "method", [1, 2, 3], 0, None, "estimate_fee"
    )


def test_simulate():
    account = Account(KEY, NETWORK)
    # Mock send
    account.send = MagicMock()

    account.simulate(account.address, "method", [1, 2, 3], max_fee=0)

    account.send.assert_called_once_with(
        account.address, "method", [1, 2, 3], 0, None, "simulate"
    )


@pytest.mark.parametrize("query_type", ["estimate_fee", "simulate"])
@patch("nile.core.account.get_nonce", return_value=0)
@patch("nile.core.account.call_or_invoke")
def test_execute_query(mock_call, mock_nonce, query_type):
    account = Account(KEY, NETWORK)

    send_args = [account.address, "method", [1, 2, 3]]
    calldata = ["111", "222", "333"]
    sig_r, sig_s = [999, 888]
    return_signature = [calldata, sig_r, sig_s]

    # Mock sign_transaction
    account.signer.sign_transaction = MagicMock(return_value=return_signature)

    account.send(
        account.address, "method", [1, 2, 3], max_fee=MAX_FEE, query_type=query_type
    )

    account.signer.sign_transaction.assert_called_once_with(
        calls=[send_args],
        nonce=0,
        sender=account.address,
        max_fee=MAX_FEE,
        version=QUERY_VERSION,
    )

    # Check query_flag is correctly passed
    mock_call.assert_called_with(
        contract=account,
        max_fee=str(MAX_FEE),
        method="__execute__",
        network=NETWORK,
        params=calldata,
        signature=[str(sig_r), str(sig_s)],
        type="invoke",
        query_flag=query_type,
    )
