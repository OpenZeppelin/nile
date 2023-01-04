"""Tests for declare command."""

import logging
from unittest.mock import patch

import pytest

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, DECLARATIONS_FILENAME
from nile.core.declare import alias_exists, declare
from nile.core.types.transactions import DeclareTransaction
from nile.utils import hex_class_hash
from nile.utils.status import TransactionStatus, TxStatus
from tests.mocks.mock_account import MockAccount


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


MOCK_ACC_ADDRESS = 0x123
MOCK_ACC_INDEX = 0
SENDER = "0x1234"
CONTRACT = "contract"
SIGNATURE = ["123", "456"]
NETWORK = "localhost"
ALIAS = "alias"
PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
OVERRIDING_PATH = ("new_path", ABIS_DIRECTORY)
MAX_FEE = 432
CALL_OUTPUT = b"output"
HASH = 111
TX_HASH = 222
TX_STATUS = TransactionStatus(TX_HASH, TxStatus.ACCEPTED_ON_L2, None)


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = hex_class_hash(HASH)
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.asyncio
@pytest.mark.parametrize("alias", ["my_contract"])
@pytest.mark.parametrize("overriding_path", [OVERRIDING_PATH, None])
@pytest.mark.parametrize("watch_mode", ["track", None])
@patch("nile.core.declare.parse_information", return_value=[HASH, TX_HASH])
@patch("nile.core.declare.deployments.register_class_hash")
@patch(
    "nile.core.types.transactions.Transaction.execute",
    return_value=(TX_STATUS, CALL_OUTPUT),
)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
async def test_declare(
    mock_get_contract_class,
    mock_execute,
    mock_register,
    mock_parse,
    caplog,
    alias,
    overriding_path,
    watch_mode,
):
    logging.getLogger().setLevel(logging.INFO)

    account = await MockAccount("TEST_KEY", NETWORK)
    with patch(
        "nile.core.types.transactions.DeclareTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = 0x777

        transaction = DeclareTransaction(
            account_address=account.address,
            contract_to_submit=CONTRACT,
            max_fee=0,
            nonce=0,
            network=account.network,
        )

        # check return value
        res = await declare(
            transaction,
            account.signer,
            alias=alias,
            watch_mode=watch_mode,
        )
        assert res == (TX_STATUS, hex_class_hash(HASH))

        # check internals
        mock_execute.assert_called_once_with(
            signer=account.signer,
            watch_mode=watch_mode,
        )
        mock_parse.assert_called_once_with(CALL_OUTPUT)
        mock_register.assert_called_once_with(HASH, account.network, alias)

        # check logs
        assert f"🚀 Declaring {CONTRACT}" in caplog.text
        assert (
            f"⏳ Successfully sent declaration of {CONTRACT} as {hex_class_hash(HASH)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@pytest.mark.asyncio
@patch("nile.core.declare.alias_exists", return_value=True)
async def test_declare_duplicate_hash(mock_alias_check):
    with pytest.raises(Exception) as err:
        await declare(ALIAS, NETWORK)

        assert (
            f"Alias {ALIAS} already exists in {NETWORK}.{DECLARATIONS_FILENAME}"
            in str(err.value)
        )
