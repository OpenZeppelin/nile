"""Test udc_helpers file."""

import logging
from unittest.mock import patch

import pytest

from nile.common import TRANSACTION_VERSION
from nile.core.types.udc_helpers import create_udc_deploy_transaction
from nile.core.types.utils import get_execute_calldata
from tests.mocks.mock_account import MockAccount

NETWORK = "localhost"


@pytest.mark.asyncio
@pytest.mark.parametrize("contract_name", ["contract"])
@pytest.mark.parametrize("salt", [0, 15, None])
@pytest.mark.parametrize("unique", [True, False])
@pytest.mark.parametrize("calldata", [[]])
@pytest.mark.parametrize("deployer_address", [0x678])
@pytest.mark.parametrize("max_fee", [0, 25, None])
@pytest.mark.parametrize("nonce", [0, 30])
@pytest.mark.parametrize("overriding_path", [None])
@pytest.mark.parametrize("exp_class_hash", [0x12345])
async def test_create_udc_deploy_transaction(
    contract_name,
    salt,
    unique,
    calldata,
    deployer_address,
    max_fee,
    nonce,
    overriding_path,
    exp_class_hash,
):
    logging.getLogger().setLevel(logging.INFO)

    account = await MockAccount("TEST_KEY", NETWORK)
    with patch("nile.core.types.udc_helpers.get_class_hash") as mock_get_class_hash:
        mock_get_class_hash.return_value = exp_class_hash

        exp_execute_calldata = get_execute_calldata(
            calls=[
                [
                    deployer_address,
                    "deployContract",
                    [
                        exp_class_hash,
                        salt or 0,
                        1 if unique else 0,
                        len(calldata),
                        *calldata,
                    ],
                ]
            ]
        )

        # check return values
        tx, predicted_address = await create_udc_deploy_transaction(
            account,
            contract_name,
            salt,
            unique,
            calldata,
            deployer_address,
            max_fee or 0,
            nonce=nonce,
        )

        assert tx.tx_type == "invoke"
        assert tx.account_address == account.address
        assert tx.calldata == exp_execute_calldata
        assert tx.max_fee == (max_fee or 0)
        assert tx.nonce == nonce
        assert tx.network == account.network
        assert tx.version == TRANSACTION_VERSION

        # check internals
        mock_get_class_hash.assert_called_once_with(contract_name, overriding_path)
