"""Tests for account commands."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from nile.core.account import Account

KEY = "TEST_KEY"
NETWORK = "goerli"
MOCK_ADDRESS = "0x123"
MOCK_INDEX = 0


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


def test_account_multiple_inits_with_same_key():
    account = Account(KEY, NETWORK)
    account.deploy()
    account2 = Account(KEY, NETWORK)

    # Check addresses don't match
    assert account.address != account2.address
    # Check indexing
    assert account.index == 0
    assert account2.index == 1


@patch("nile.core.account.deploy", return_value=(1, 2))
def test_deploy(mock_deploy):
    account = Account(KEY, NETWORK)
    with patch("nile.core.account.os.path.dirname") as mock_path:
        test_path = "/overriding_path"
        mock_path.return_value.replace.return_value = test_path

        account.deploy()

        mock_deploy.assert_called_with(
            "Account",
            [str(account.signer.public_key)],
            NETWORK,
            f"account-{account.index + 1}",
            (f"{test_path}/artifacts", f"{test_path}/artifacts/abis"),
        )


@patch("nile.core.account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.accounts.register")
def test_deploy_accounts_register(mock_register, mock_deploy):
    account = Account(KEY, NETWORK)

    mock_register.assert_called_once_with(
        account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, NETWORK
    )


@patch("nile.core.account.call_or_invoke")
def test_send_nonce_call(mock_call):
    account = Account(KEY, NETWORK)
    contract_address, _ = account.deploy()

    # Instead of creating and populating a tmp .txt file, this uses the
    # deployed account address (contract_address) as the target
    account.send(contract_address, "method", [1, 2, 3], max_fee=1)

    # 'call_or_invoke' is called twice ('get_nonce' and '__execute__')
    assert mock_call.call_count == 2

    # Check 'get_nonce' call
    mock_call.assert_any_call(account.address, "call", "get_nonce", [], NETWORK)


@pytest.mark.parametrize(
    "callarray, calldata",
    # The following callarray and calldata args tests the Account's list comprehensions
    # ensuring they're set to strings and passed correctly
    [([[111]], []), ([[111, 222]], [333, 444, 555])],
)
def test_send_sign_transaction_and_execute(callarray, calldata):
    account = Account(KEY, NETWORK)
    contract_address, _ = account.deploy()

    sig_r, sig_s = [999, 888]
    return_signature = [callarray, calldata, sig_r, sig_s]

    account.signer.sign_transaction = MagicMock(return_value=return_signature)

    with patch("nile.core.account.call_or_invoke") as mock_call:
        send_args = [contract_address, "method", [1, 2, 3]]
        nonce = 4
        max_fee = 1
        account.send(*send_args, max_fee, nonce)

        # Check values are correctly passed to 'sign_transaction'
        account.signer.sign_transaction.assert_called_once_with(
            calls=[send_args], nonce=nonce, sender=account.address, max_fee=1
        )

        # Check values are correctly passed to '__execute__'
        mock_call.assert_called_with(
            contract=account.address,
            max_fee=str(max_fee),
            method="__execute__",
            network=NETWORK,
            params=[
                str(len(callarray)),
                *(str(elem) for sublist in callarray for elem in sublist),
                str(len(calldata)),
                *(str(param) for param in calldata),
                str(nonce),
            ],
            signature=[str(sig_r), str(sig_s)],
            type="invoke",
        )
