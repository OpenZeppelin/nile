"""Tests for declare command."""
import logging
from unittest.mock import Mock, mock_open, patch

import pytest
from starkware.starknet.definitions import constants
from starkware.starknet.services.api.gateway.transaction import (
    DECLARE_SENDER_ADDRESS,
    Declare,
)

from nile.common import BUILD_DIRECTORY, DECLARATIONS_FILENAME
from nile.core.declare import alias_exists, declare


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
PATH = "p"
HASH = 111
TX_HASH = 222


class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        sup = super()

        async def coro():
            return sup.__call__(*args, **kwargs)

        return coro()


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = HASH
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.asyncio
async def test_declare(caplog):
    logging.getLogger().setLevel(logging.INFO)

    with patch(
        "nile.core.declare.get_gateway_response", new=AsyncMock()
    ) as mock_response:
        mock_response.return_value = dict(
            {"class_hash": HASH, "transaction_hash": TX_HASH}
        )

        with patch("nile.core.declare.open", new_callable=mock_open):
            with patch("nile.core.declare.ContractClass") as mock_contract_class:
                res = await declare(contract_name=CONTRACT, network=NETWORK)
                assert res == HASH, TX_HASH

                # check passed args to response
                mock_response.assert_called_once_with(
                    network=NETWORK,
                    tx=Declare(
                        version=constants.TRANSACTION_VERSION,
                        contract_class=mock_contract_class.loads(),
                        sender_address=DECLARE_SENDER_ADDRESS,
                        max_fee=0,
                        signature=[],
                        nonce=0,
                    ),
                    token=None,
                )

                # check logs
                assert f"🚀 Declaring {CONTRACT}" in caplog.text
                assert (
                    f"📦 Registering {HASH} in {NETWORK}.declarations.txt" in caplog.text
                )
                assert (
                    f"⏳ Declaration of {CONTRACT} successfully sent at {HASH}"
                    in caplog.text
                )
                assert f"🧾 Transaction hash: {TX_HASH}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_register",
    [
        (
            {"contract_name": CONTRACT, "network": NETWORK},  # args
            [HASH, NETWORK, None],  # expected register
        ),
        (
            {"contract_name": CONTRACT, "network": NETWORK, "alias": ALIAS},  # args
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            {
                "contract_name": CONTRACT,
                "network": NETWORK,
                "alias": ALIAS,
                "overriding_path": PATH,
            },  # args
            [HASH, NETWORK, ALIAS],  # expected register
        ),
    ],
)
async def test_declare_register(args, exp_register):
    with patch(
        "nile.core.declare.get_gateway_response", new=AsyncMock()
    ) as mock_response:
        mock_response.return_value = dict(
            {"class_hash": HASH, "transaction_hash": TX_HASH}
        )

        with patch("nile.core.declare.open", new_callable=mock_open) as m_open:
            with patch("nile.core.declare.ContractClass"):
                with patch(
                    "nile.core.declare.deployments.register_class_hash"
                ) as mock_register:

                    await declare(**args)

                    # check overriding path
                    base_path = (
                        PATH if "overriding_path" in args.keys() else BUILD_DIRECTORY
                    )
                    m_open.assert_called_once_with(f"{base_path}/{CONTRACT}.json", "r")

                    # check registration
                    mock_register.assert_called_once_with(*exp_register)


@pytest.mark.asyncio
@patch("nile.core.declare.alias_exists", return_value=True)
async def test_declare_duplicate_hash(mock_alias_check):
    with pytest.raises(Exception) as err:
        await declare(ALIAS, NETWORK)

        assert (
            f"Alias {ALIAS} already exists in {NETWORK}.{DECLARATIONS_FILENAME}"
            in str(err.value)
        )
