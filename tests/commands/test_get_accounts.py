"""Tests for get-accounts command."""
import logging
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import MissingSchema

from nile.core.account import Account
from nile.utils import hex_address
from nile.utils import normalize_number as normalize
from nile.utils.get_accounts import (
    _check_and_return_account,
    get_accounts,
    get_predeployed_accounts,
)
from tests.mocks.mock_response import MockResponse

NETWORK = "localhost"
GATEWAYS = {"localhost": "http://127.0.0.1:5050/"}
PUBKEYS = [
    883045738439352841478194533192765345509759306772397516907181243450667673002,
    661519931401775515888740911132355225260405929679788917190706536765421826262,
]
ADDRESSES = [333, 333]
INDEXES = [0, 1]
ALIASES = ["TEST_KEY", "TEST_KEY_2"]


MOCK_ADDRESS = 0x123
MOCK_INDEX = 0

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
JSON_DATA = [
    {
        "address": normalize("0xaaa1"),
        "private_key": normalize("0xbbb1"),
        "public_key": normalize("0xbbb2"),
    },
    {
        "address": normalize("0xaaa2"),
        "private_key": normalize("0xbbb3"),
        "public_key": normalize("0xbbb4"),
    },
]


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "private_keys, public_keys",
    [
        ([ALIASES[0], PUBKEYS[0]]),
        ([ALIASES[1], PUBKEYS[1]]),
    ],
)
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
async def test__check_and_return_account_with_matching_keys(
    mock_deploy, private_keys, public_keys
):
    # Check matching public/private keys
    account = await _check_and_return_account(private_keys, public_keys, NETWORK)

    assert type(account) is Account


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "private_keys, public_keys",
    [
        ([ALIASES[0], PUBKEYS[1]]),
        ([ALIASES[1], PUBKEYS[0]]),
    ],
)
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
async def test__check_and_return_account_with_mismatching_keys(
    mock_deploy, private_keys, public_keys
):
    # Check mismatched public/private keys
    with pytest.raises(AssertionError) as err:
        await _check_and_return_account(private_keys, public_keys, NETWORK)

    assert "Signer pubkey does not match deployed pubkey" in str(err.value)


@pytest.mark.asyncio
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
async def test_get_accounts_no_activated_accounts_feedback(mock_deploy, capsys):
    await get_accounts(NETWORK)
    # This test uses capsys in order to test the print statements (instead of logging)
    captured = capsys.readouterr()

    assert (
        f"❌ No registered accounts detected in {NETWORK}.accounts.json" in captured.out
    )
    assert (
        "For more info, see https://github.com/OpenZeppelin/nile#get-accounts"
        in captured.out
    )


@pytest.mark.asyncio
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.utils.get_accounts.current_index", MagicMock(return_value=len(PUBKEYS)))
@patch("nile.utils.get_accounts.open", MagicMock())
@patch("nile.utils.get_accounts.json.load", MagicMock(return_value=MOCK_ACCOUNTS))
async def test_get_accounts_activated_accounts_feedback(mock_deploy, caplog):
    logging.getLogger().setLevel(logging.INFO)

    # Default argument
    await get_accounts(NETWORK)

    # Check total accounts log
    assert f"\nTotal registered accounts: {len(PUBKEYS)}\n" in caplog.text

    # Check index/address log
    for i in range(len(PUBKEYS)):
        assert f"{INDEXES[i]}: {hex_address(ADDRESSES[i])}" in caplog.text

    # Check final success log
    assert "\n🚀 Successfully retrieved deployed accounts" in caplog.text


@pytest.mark.asyncio
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.utils.get_accounts.current_index", MagicMock(return_value=len(PUBKEYS)))
@patch("nile.utils.get_accounts.open", MagicMock())
@patch("nile.utils.get_accounts.json.load", MagicMock(return_value=MOCK_ACCOUNTS))
async def test_get_accounts_with_keys(mock_deploy):
    with patch(
        "nile.utils.get_accounts._check_and_return_account"
    ) as mock_return_account:
        result = await get_accounts(NETWORK)

        # Check correct args are passed to `_check_and_receive_account`
        for i in range(len(PUBKEYS)):
            mock_return_account.assert_any_call(ALIASES[i], PUBKEYS[i], NETWORK)

        # Assert call count equals correct number of accounts
        assert mock_return_account.call_count == len(PUBKEYS)

        # Assert returned accounts array equals correct number of accounts
        assert len(result) == len(PUBKEYS)


@pytest.mark.asyncio
@patch("nile.common.get_gateways", return_value=GATEWAYS)
@patch("nile.utils.get_accounts._check_and_return_account")
@patch("requests.get", return_value=MockResponse(JSON_DATA, 200))
async def test_get_predeployed_accounts(
    mock_response, mock_return_account, mock_gateways
):
    result = await get_predeployed_accounts("localhost")

    # Assert the correct endpoint is used
    mock_response.assert_called_once_with(
        f"{GATEWAYS.get('localhost')}/predeployed_accounts"
    )

    # Check correct args are passed to `_check_and_receive_account`
    for i in range(len(JSON_DATA)):
        predeployed_info = {
            "address": JSON_DATA[i]["address"],
            "alias": f"account-{i}",
            "index": i,
        }
        mock_return_account.assert_any_call(
            JSON_DATA[i]["private_key"],
            JSON_DATA[i]["public_key"],
            "localhost",
            predeployed_info,
        )

    # Assert call count equals correct number of accounts
    assert mock_return_account.call_count == len(JSON_DATA)

    # Assert returned accounts array equals correct number of accounts
    assert len(result) == len(JSON_DATA)


@pytest.mark.asyncio
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.common.get_gateways", return_value=GATEWAYS)
@patch("nile.utils.get_accounts._check_and_return_account")
@patch("requests.get", return_value=MockResponse(JSON_DATA, 200))
async def test_get_predeployed_accounts_logging(
    mock_response, mock_return_account, mock_gateways, mock_deploy, caplog
):
    # make logs visible to test
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
    await get_predeployed_accounts("localhost")

    assert "🚀 Successfully retrieved pre-deployed accounts" in caplog.text

    # test exceptions
    logger.setLevel(logging.ERROR)

    # test missing schema first
    mock_response.side_effect = MissingSchema
    await get_predeployed_accounts("localhost")

    assert "❌ Failed to retrieve gateway from provided network" in caplog.text

    # test generic exceptions
    mock_response.side_effect = Exception
    await get_predeployed_accounts("localhost")

    assert "❌ Error querying the account from the gateway" in caplog.text
    assert "Check you are connected to a starknet-devnet implementation" in caplog.text
