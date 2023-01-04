"""Test tx wrappers module."""

from unittest.mock import patch

import pytest

from nile.core.types.transactions import (
    DeclareTransaction,
    DeployAccountTransaction,
    InvokeTransaction,
)
from nile.core.types.tx_wrappers import (
    BaseTxWrapper,
    DeclareTxWrapper,
    DeployAccountTxWrapper,
    DeployContractTxWrapper,
)
from tests.mocks.mock_account import MockAccount

TX_HASH = 123
KEY = "TEST_KEY"
NETWORK = "localhost"


@pytest.mark.asyncio
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch("nile.core.types.transactions.Transaction.execute", return_value="ret")
async def test_base_wrapper_execute(
    mock_execute,
    watch_mode,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()
        base = BaseTxWrapper(tx, account)

        assert base.tx == tx
        assert base.account == account

        ret = await base.execute(watch_mode=watch_mode)

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_execute.assert_called_once_with(
            signer=account.signer, watch_mode=watch_mode
        )


@pytest.mark.asyncio
@patch("nile.core.types.transactions.Transaction.estimate_fee", return_value="ret")
async def test_base_wrapper_estimate_fee(
    mock_estimate_fee,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()
        base = BaseTxWrapper(tx, account)

        assert base.tx == tx
        assert base.account == account

        ret = await base.estimate_fee()

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_estimate_fee.assert_called_once_with(signer=account.signer)


@pytest.mark.asyncio
@patch("nile.core.types.transactions.Transaction.simulate", return_value="ret")
async def test_base_wrapper_simulate(
    mock_simulate,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()
        base = BaseTxWrapper(tx, account)

        assert base.tx == tx
        assert base.account == account

        ret = await base.simulate()

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_simulate.assert_called_once_with(signer=account.signer)


@pytest.mark.asyncio
@pytest.mark.parametrize("max_fee", [0, 15])
@patch("nile.core.types.transactions.Transaction.execute", return_value="ret")
@patch("nile.core.types.transactions.Transaction.update_fee")
async def test_base_wrapper_update_fee(
    mock_update_fee,
    mock_execute,
    max_fee,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()
        base = BaseTxWrapper(tx, account)

        assert base.tx == tx
        assert base.account == account

        base.update_fee(max_fee=max_fee)

        mock_update_fee.assert_called_once_with(max_fee=max_fee)

        # Validate chaining is allowed
        output = await base.update_fee(max_fee=max_fee + 1).execute()

        assert output == "ret"


@pytest.mark.asyncio
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.tx_wrappers.declare", return_value="ret")
async def test_declare_wrapper_execute(
    mock_declare,
    mock_get_contract_class,
    watch_mode,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.DeclareTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeclareTransaction()
        wrapper = DeclareTxWrapper(tx, account, alias="alias")

        assert wrapper.tx == tx
        assert wrapper.account == account
        assert wrapper.alias == "alias"

        ret = await wrapper.execute(watch_mode=watch_mode)

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_declare.assert_called_once_with(
            transaction=wrapper.tx,
            signer=wrapper.account.signer,
            alias=wrapper.alias,
            watch_mode=watch_mode,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch("nile.core.types.tx_wrappers.deploy_contract", return_value="ret")
async def test_deploy_contract_wrapper_execute(
    mock_deploy_contract,
    watch_mode,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()
        wrapper = DeployContractTxWrapper(
            tx,
            account,
            alias="alias",
            contract_name="contract",
            overriding_path="path",
            predicted_address=0x345,
            abi="abi",
        )

        assert wrapper.tx == tx
        assert wrapper.account == account
        assert wrapper.alias == "alias"
        assert wrapper.overriding_path == "path"
        assert wrapper.contract_name == "contract"
        assert wrapper.predicted_address == 0x345
        assert wrapper.abi == "abi"

        ret = await wrapper.execute(watch_mode=watch_mode)

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_deploy_contract.assert_called_once_with(
            transaction=wrapper.tx,
            signer=wrapper.account.signer,
            contract_name=wrapper.contract_name,
            alias=wrapper.alias,
            predicted_address=wrapper.predicted_address,
            overriding_path=wrapper.overriding_path,
            abi=wrapper.abi,
            watch_mode=watch_mode,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.transactions.get_class_hash", return_value=777)
@patch("nile.core.types.tx_wrappers.deploy_account", return_value="ret")
async def test_deploy_account_wrapper_execute(
    mock_deploy_account,
    mock_get_class_hash,
    mock_get_contract_class,
    watch_mode,
):
    account = await MockAccount(KEY, NETWORK)
    with patch(
        "nile.core.types.transactions.DeployAccountTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeployAccountTransaction(
            contract_to_submit="contract", overriding_path="path"
        )
        wrapper = DeployAccountTxWrapper(
            tx,
            account,
            alias="alias",
            abi="abi",
        )

        assert wrapper.tx == tx
        assert wrapper.account == account
        assert wrapper.alias == "alias"
        assert wrapper.abi == "abi"

        ret = await wrapper.execute(watch_mode=watch_mode)

        # Check return value
        assert ret == "ret"

        # Check internals
        mock_deploy_account.assert_called_once_with(
            transaction=wrapper.tx,
            account=wrapper.account,
            contract_name=wrapper.tx.contract_to_submit,
            alias=wrapper.alias,
            predicted_address=wrapper.tx.predicted_address,
            overriding_path=wrapper.tx.overriding_path,
            abi=wrapper.abi,
            watch_mode=watch_mode,
        )
