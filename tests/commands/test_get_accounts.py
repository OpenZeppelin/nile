"""Tests for get-accounts command."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from nile.core.account import Account
from nile.utils.get_accounts import _check_and_return_account, get_accounts

NETWORK = "goerli"
PUBKEYS = [
    "883045738439352841478194533192765345509759306772397516907181243450667673002",
    "661519931401775515888740911132355225260405929679788917190706536765421826262",
]
ADDRESSES = ["333", "444"]
INDEXES = [0, 1]
ALIASES = ["TEST_KEY", "TEST_KEY_2"]

MOCK_ACCOUNTS = {
    PUBKEYS[0]: {
        "address": ADDRESSES[0],
        "index": INDEXES[0],
        "alias": ALIASES[0],
    },
    PUBKEYS[1]: {
        "address": ADDRESSES[1],
        "index": INDEXES[1],
        "alias": ALIASES[1],
    },
}


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def mock_subprocess():
    with patch("nile.core.compile.subprocess") as mock_subprocess:
        yield mock_subprocess


@pytest.mark.parametrize(
    "private_keys, public_keys",
    [
        ([ALIASES[0], PUBKEYS[0]]),
        ([ALIASES[1], PUBKEYS[1]]),
    ],
)
def test__check_and_return_account_with_matching_keys(private_keys, public_keys):
    # Check matching public/private keys
    account = _check_and_return_account(private_keys, public_keys, NETWORK)

    assert type(account) is Account


@pytest.mark.parametrize(
    "private_keys, public_keys",
    [
        ([ALIASES[0], PUBKEYS[1]]),
        ([ALIASES[1], PUBKEYS[0]]),
    ],
)
def test__check_and_return_account_with_mismatching_keys(private_keys, public_keys):
    # Check mismatched public/private keys
    with pytest.raises(AssertionError) as err:
        _check_and_return_account(private_keys, public_keys, NETWORK)

    assert "Signer pubkey does not match deployed pubkey" in str(err.value)


def test_get_accounts_no_activated_accounts_feedback(capsys):
    get_accounts(NETWORK)
    # This test uses capsys in order to test the print statements (instead of logging)
    captured = capsys.readouterr()

    assert (
        f"❌ No registered accounts detected in {NETWORK}.accounts.json" in captured.out
    )
    assert (
        "For more info, see https://github.com/OpenZeppelin/nile#get-accounts"
        in captured.out
    )


@patch("nile.utils.get_accounts.current_index", MagicMock(return_value=len(PUBKEYS)))
@patch("nile.utils.get_accounts.open", MagicMock())
@patch("nile.utils.get_accounts.json.load", MagicMock(return_value=MOCK_ACCOUNTS))
def test_get_accounts_activated_accounts_feedback(caplog):
    logging.getLogger().setLevel(logging.INFO)

    # Default argument
    get_accounts(NETWORK)

    # Check total accounts log
    assert f"\nTotal registered accounts: {len(PUBKEYS)}\n" in caplog.text

    # Check index/address log
    for i in range(len(PUBKEYS)):
        assert f"{INDEXES[i]}: {ADDRESSES[i]}" in caplog.text

    # Check final success log
    assert "\n🚀 Successfully retrieved deployed accounts" in caplog.text


@patch("nile.utils.get_accounts.current_index", MagicMock(return_value=len(PUBKEYS)))
@patch("nile.utils.get_accounts.open", MagicMock())
@patch("nile.utils.get_accounts.json.load", MagicMock(return_value=MOCK_ACCOUNTS))
def test_get_accounts_with_keys():

    with patch(
        "nile.utils.get_accounts._check_and_return_account"
    ) as mock_return_account:
        result = get_accounts(NETWORK)

        # Check correct args are passed to `_check_and_receive_account`
        for i in range(len(PUBKEYS)):
            mock_return_account.assert_any_call(ALIASES[i], PUBKEYS[i], NETWORK)

        # Assert call count equals correct number of accounts
        assert mock_return_account.call_count == len(PUBKEYS)

        # assert returned accounts array equals correct number of accounts
        assert len(result) == len(PUBKEYS)
