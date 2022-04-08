"""Tests for account commands."""
import pytest
from unittest.mock import patch

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


def test_account_init_account_exists():
    account = Account(KEY, NETWORK)
    account.deploy()
    account2 = Account(KEY, NETWORK)
    # Check addresses don't match
    assert account.address != account2.address
    # Check indexing
    assert account.index == 0
    assert account2.index == 1    


@patch("nile.core.account.deploy")
def test_deploy_accounts_register(mock_deploy):
    mock_deploy.return_value = MOCK_ADDRESS, MOCK_INDEX

    with patch("nile.core.account.accounts.register") as mock_register:
        account = Account(KEY, NETWORK)

        mock_register.assert_called_once_with(
            account.signer.public_key,
            MOCK_ADDRESS,
            MOCK_INDEX,
            NETWORK
        )

@patch("nile.core.account.Account")
def test_send_sign_transaction(mock_account):
    account = Account(KEY, NETWORK)
    addr, _ = account.deploy()
    # Instead of creating and populating a tmp .txt file, this uses the
    # deployed account address as the target
    args = [addr, "method", [1, 2, 3]]

    with patch("nile.core.account.call_or_invoke") as mock_call:
        account.send(*args)
        assert mock_call.call_count == 2

        # Check 'get_nonce' call
        mock_call.assert_any_call(
            account.address, 'call', 'get_nonce', [], 'goerli'
        )

        mock_account = mock_call.call_args_list
        print(mock_account)
        
 