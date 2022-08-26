"""Tests for deploy command."""
import logging
from unittest.mock import patch, Mock, mock_open

import pytest
from starkware.starknet.definitions import constants
from starkware.starknet.services.api.gateway.transaction import Deploy
from nile.core.deploy import ABIS_DIRECTORY, BUILD_DIRECTORY, deploy


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        sup = super()

        async def coro():
            return sup.__call__(*args, **kwargs)

        return coro()


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
ABI = f"{ABIS_DIRECTORY}/{CONTRACT}.json"
PATH2 = "artifacts2"
PATH_OVERRIDE = (PATH2, ABIS_DIRECTORY)
ARGS = [1, 2, 3]
ADDRESS = 999
TX_HASH = 222
SALT = "0x123"
RESPONSE = dict({"address": ADDRESS, "transaction_hash": TX_HASH})


@pytest.mark.asyncio
async def test_deploy(caplog):
    logging.getLogger().setLevel(logging.INFO)

    with patch(
        "nile.core.deploy.get_gateway_response", new=AsyncMock()
    ) as mock_response:
        mock_response.return_value = RESPONSE
        with patch("nile.core.deploy.open", new_callable=mock_open):
            with patch("nile.core.deploy.ContractClass") as mock_contract_class:
                res = await deploy(
                    contract_name=CONTRACT,
                    arguments=ARGS,
                    network=NETWORK,
                    alias=ALIAS,
                    salt=SALT
                )

                # check return values
                assert res == (ADDRESS, ABI)

                # check response
                mock_response.assert_called_once_with(
                    network=NETWORK,
                    tx=Deploy(
                        version=constants.TRANSACTION_VERSION,
                        contract_address_salt=int(SALT, 16),
                        contract_definition=mock_contract_class.loads(),
                        constructor_calldata=ARGS
                    ),
                    token=None,
                )

    ## check logs
    assert f"🚀 Deploying {CONTRACT}" in caplog.text
    assert f"⏳ ️Deployment of {CONTRACT} successfully sent at {ADDRESS}" in caplog.text
    assert f"🧾 Transaction hash: {TX_HASH}" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_register",
    [
        (
            {
                "contract_name": CONTRACT,
                "arguments": ARGS,
                "network": NETWORK,
                "alias": None
            },
            [ADDRESS, ABI, NETWORK, None],  # expected register
        ),
        (
            {
                "contract_name": CONTRACT,
                "arguments": ARGS,
                "network": NETWORK,
                "alias": ALIAS,
                "overriding_path": PATH_OVERRIDE
            },
            [ADDRESS, ABI, NETWORK, ALIAS],  # expected register
        ),
    ],
)
async def test_deploy_registration(args, exp_register):
    with patch(
        "nile.core.deploy.get_gateway_response", new=AsyncMock()
    ) as mock_response:
        mock_response.return_value = RESPONSE
        with patch("nile.core.deploy.open", new_callable=mock_open) as m_open:
            with patch("nile.core.deploy.ContractClass"):
                with patch(
                    "nile.core.deploy.deployments.register"
                ) as mock_register:

                    await deploy(**args)

                    # check overriding path
                    base_path = (
                        PATH2 if "overriding_path" in args.keys() else BUILD_DIRECTORY
                    )
                    m_open.assert_called_once_with(f"{base_path}/{CONTRACT}.json", "r")
                    mock_register.assert_called_once_with(
                        *exp_register
                    )
