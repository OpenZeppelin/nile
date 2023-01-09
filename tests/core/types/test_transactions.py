"""Test transactions module."""

import logging
from unittest.mock import patch

import pytest

from nile.common import (
    NETWORKS_CHAIN_ID,
    NILE_ABIS_DIR,
    QUERY_VERSION_BASE,
    TRANSACTION_VERSION,
)
from nile.core.types.transactions import (
    DeclareTransaction,
    DeployAccountTransaction,
    InvokeTransaction,
)
from nile.utils import hex_address
from nile.utils.status import TransactionStatus, TxStatus
from tests.mocks.mock_account import MockAccount

TX_HASH = 123
TX_HASH_2 = 1234
KEY = "TEST_KEY"
NETWORK = "localhost"
TX_STATUS = TransactionStatus(TX_HASH, TxStatus.ACCEPTED_ON_L2, None)


@pytest.mark.asyncio
@pytest.mark.parametrize("account_address", [0x1, 0x2, 0x3])
@pytest.mark.parametrize("max_fee", [0, 15, None])
@pytest.mark.parametrize("nonce", [0, 10, None])
@pytest.mark.parametrize("network", ["localhost", "goerli2", "mainnet"])
@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("entry_point", [None])
@pytest.mark.parametrize("calldata", [[]])
@patch("nile.core.types.transactions.Transaction._validate")
async def test_invoke_transaction_init(
    mock_validate,
    account_address,
    max_fee,
    nonce,
    network,
    version,
    entry_point,
    calldata,
):
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction(
            account_address=account_address,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
            entry_point=entry_point,
            calldata=calldata,
        )

        assert tx.tx_type == "invoke"
        assert tx.entry_point == entry_point
        assert tx.calldata == calldata
        assert tx.account_address == account_address
        assert tx.max_fee == max_fee or 0
        assert tx.nonce == nonce
        assert tx.network == network
        assert tx.version == version
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID[network]

        # Check internals
        mock_validate.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("account_address", [0x1, 0x2, 0x3])
@pytest.mark.parametrize("max_fee", [0, 15, None])
@pytest.mark.parametrize("nonce", [0, 10])
@pytest.mark.parametrize("network", ["localhost", "goerli2", "mainnet"])
@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("contract_to_submit", ["contract"])
@pytest.mark.parametrize("overriding_path", [None])
@patch("nile.core.types.transactions.Transaction._validate")
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
async def test_declare_transaction_init(
    mock_validate,
    mock_get_class,
    account_address,
    max_fee,
    nonce,
    network,
    version,
    contract_to_submit,
    overriding_path,
):
    with patch(
        "nile.core.types.transactions.DeclareTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeclareTransaction(
            account_address=account_address,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
            contract_to_submit=contract_to_submit,
            overriding_path=overriding_path,
        )

        assert tx.tx_type == "declare"
        assert tx.contract_to_submit == contract_to_submit
        assert tx.contract_class == "ContractClass"
        assert tx.overriding_path == overriding_path
        assert tx.account_address == account_address
        assert tx.max_fee == max_fee or 0
        assert tx.nonce == nonce
        assert tx.network == network
        assert tx.version == version
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID[network]

        # Check internals
        mock_validate.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("account_address", [0x1, 0x2, 0x3])
@pytest.mark.parametrize("max_fee", [0, 15, None])
@pytest.mark.parametrize("nonce", [0, 10])
@pytest.mark.parametrize("network", ["localhost", "goerli2", "mainnet"])
@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("contract_to_submit", ["contract"])
@pytest.mark.parametrize("calldata", [[]])
@pytest.mark.parametrize("overriding_path", [None])
@patch("nile.core.types.transactions.Transaction._validate")
@patch("nile.core.types.transactions.get_class_hash", return_value=777)
async def test_deploy_account_transaction_init(
    mock_get_class_hash,
    mock_validate,
    account_address,
    max_fee,
    nonce,
    network,
    version,
    contract_to_submit,
    calldata,
    overriding_path,
):
    with patch(
        "nile.core.types.transactions.DeployAccountTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeployAccountTransaction(
            account_address=account_address,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
            contract_to_submit=contract_to_submit,
            calldata=calldata,
            overriding_path=overriding_path,
        )

        assert tx.tx_type == "deploy_account"
        assert tx.contract_to_submit == contract_to_submit
        assert tx.calldata == calldata
        assert tx.class_hash == 777
        assert tx.overriding_path == overriding_path
        assert tx.account_address == account_address
        assert tx.max_fee == max_fee or 0
        assert tx.nonce == nonce
        assert tx.network == network
        assert tx.version == version
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID[network]

        # Check internals
        mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_invoke_transaction_init_defaults():
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()

        assert tx.tx_type == "invoke"
        assert tx.entry_point == "__execute__"
        assert tx.calldata is None
        assert tx.account_address == 0
        assert tx.max_fee == 0
        assert tx.nonce == 0
        assert tx.network == "localhost"
        assert tx.version == TRANSACTION_VERSION
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID["localhost"]


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
async def test_declare_transaction_init_defaults(mock_get_contract_class):
    with patch(
        "nile.core.types.transactions.DeclareTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeclareTransaction()

        assert tx.tx_type == "declare"
        assert tx.contract_to_submit is None
        assert tx.contract_class == "ContractClass"
        assert tx.overriding_path is None
        assert tx.account_address == 0
        assert tx.max_fee == 0
        assert tx.nonce == 0
        assert tx.network == "localhost"
        assert tx.version == TRANSACTION_VERSION
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID["localhost"]


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_class_hash", return_value=777)
async def test_deploy_account_transaction_init_defaults(mock_get_class_hash):
    with patch(
        "nile.core.types.transactions.DeployAccountTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = DeployAccountTransaction()

        assert tx.tx_type == "deploy_account"
        assert tx.contract_to_submit is None
        assert tx.calldata is None
        assert tx.class_hash == 777
        assert tx.overriding_path is None
        assert tx.account_address == 0
        assert tx.max_fee == 0
        assert tx.nonce == 0
        assert tx.network == "localhost"
        assert tx.version == TRANSACTION_VERSION
        assert tx.hash == TX_HASH
        assert tx.query_hash == TX_HASH
        assert tx.chain_id == NETWORKS_CHAIN_ID["localhost"]

        assert tx.overriding_path is None


@pytest.mark.asyncio
@pytest.mark.parametrize("watch_mode", [None, "track", "debug"])
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_tx_hash",
    return_value=TX_HASH,
)
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_execute_call_args",
    return_value={"param": "value"},
)
@patch(
    "nile.core.types.transactions.status",
    return_value=TX_STATUS,
)
async def test_transaction_execute(
    mock_status, mock_call_args, mock_get_tx_hash, watch_mode
):

    account = await MockAccount(KEY, NETWORK)
    mock_sig_r, mock_sig_s = account.signer.sign(TX_HASH)
    with patch("nile.core.types.transactions.execute_call") as mock_execute_call:
        mock_execute_call.return_value = f"Transaction hash: {hex(TX_HASH)}"

        tx = InvokeTransaction()

        tx_status, output = await tx.execute(
            account.signer, watch_mode=watch_mode, extra_param="extra_value"
        )

        assert tx_status == TX_STATUS
        assert output == f"Transaction hash: {hex(TX_HASH)}"

        # Check internals
        mock_execute_call.assert_called_once_with(
            tx.tx_type,
            tx.network,
            signature=[mock_sig_r, mock_sig_s],
            max_fee=tx.max_fee,
            query_flag=None,
            param="value",
            extra_param="extra_value",
        )
        mock_status.assert_called_once_with(tx.hash, tx.network, watch_mode)


@pytest.mark.asyncio
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_tx_hash",
    return_value=TX_HASH,
)
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_execute_call_args",
    return_value={"param": "value"},
)
async def test_transaction_estimate_fee(mock_call_args, mock_get_tx_hash, caplog):

    account = await MockAccount(KEY, NETWORK)
    mock_sig_r, mock_sig_s = account.signer.sign(TX_HASH)
    exp_output = 1000
    with patch("nile.core.types.transactions.execute_call") as mock_execute_call:
        mock_execute_call.return_value = f"The estimated fee is: {exp_output}"

        tx = InvokeTransaction()

        # make logs visible to test
        logging.getLogger().setLevel(logging.INFO)

        output = await tx.estimate_fee(account.signer, extra_param="extra_value")

        assert output == exp_output

        # Check internals
        mock_execute_call.assert_called_once_with(
            tx.tx_type,
            tx.network,
            signature=[mock_sig_r, mock_sig_s],
            max_fee=tx.max_fee,
            query_flag="estimate_fee",
            param="value",
            extra_param="extra_value",
        )

        # Check logs
        assert f"The estimated fee is: {exp_output}" in caplog.text


@pytest.mark.asyncio
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_tx_hash",
    return_value=TX_HASH,
)
@patch(
    "nile.core.types.transactions.InvokeTransaction._get_execute_call_args",
    return_value={"param": "value"},
)
async def test_transaction_simulate(mock_call_args, mock_get_tx_hash, caplog):

    account = await MockAccount(KEY, NETWORK)
    mock_sig_r, mock_sig_s = account.signer.sign(TX_HASH)
    with patch("nile.core.types.transactions.execute_call") as mock_execute_call:
        mock_execute_call.return_value = '\n\n\n\n{"response" : "simulated"}'

        tx = InvokeTransaction()

        # make logs visible to test
        logging.getLogger().setLevel(logging.INFO)

        output = await tx.simulate(account.signer, extra_param="extra_value")

        assert output == {"response": "simulated"}

        # Check internals
        mock_execute_call.assert_called_once_with(
            tx.tx_type,
            tx.network,
            signature=[mock_sig_r, mock_sig_s],
            max_fee=tx.max_fee,
            query_flag="simulate",
            param="value",
            extra_param="extra_value",
        )

        # Check logs
        assert '\n\n\n\n{"response" : "simulated"}' in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("max_fee", [0, 15])
@patch("nile.core.types.transactions.Transaction.execute", return_value="output")
async def test_transaction_update_fee(mock_execute, max_fee):
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction(max_fee=0)

        mock_get_tx_hash.return_value = TX_HASH_2

        tx.update_fee(max_fee=max_fee)

        assert tx.max_fee == max_fee
        assert tx.hash == TX_HASH_2
        assert tx.query_hash == TX_HASH_2

        # Validate chaining is allowed
        output = await tx.update_fee(max_fee=max_fee + 1).execute()

        assert output == "output"


@pytest.mark.asyncio
async def test_transaction_validate():
    with patch(
        "nile.core.types.transactions.InvokeTransaction._get_tx_hash"
    ) as mock_get_tx_hash:
        mock_get_tx_hash.return_value = TX_HASH

        tx = InvokeTransaction()

        tx.hash = 0

        with pytest.raises(Exception) as e_info:
            tx._validate()

        assert (
            str(e_info.value) == "Transaction hash is empty after transaction creation!"
        )


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_invoke_hash", return_value=TX_HASH)
async def test_invoke_get_tx_hash(mock_get_invoke_hash):
    tx = InvokeTransaction()

    # Assert call for tx_hash
    mock_get_invoke_hash.assert_any_call(
        tx.account_address,
        tx.calldata,
        tx.max_fee,
        tx.nonce,
        TRANSACTION_VERSION,
        tx.chain_id,
    )

    # Assert call for query_hash
    mock_get_invoke_hash.assert_any_call(
        tx.account_address,
        tx.calldata,
        tx.max_fee,
        tx.nonce,
        QUERY_VERSION_BASE + TRANSACTION_VERSION,
        tx.chain_id,
    )


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_declare_hash", return_value=TX_HASH)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
async def test_declare_get_tx_hash(mock_get_contract_class, mock_get_declare_hash):
    tx = DeclareTransaction()

    # Assert call for tx_hash
    mock_get_declare_hash.assert_any_call(
        tx.account_address,
        tx.contract_class,
        tx.max_fee,
        tx.nonce,
        TRANSACTION_VERSION,
        tx.chain_id,
    )

    # Assert call for query_hash
    mock_get_declare_hash.assert_any_call(
        tx.account_address,
        tx.contract_class,
        tx.max_fee,
        tx.nonce,
        QUERY_VERSION_BASE + TRANSACTION_VERSION,
        tx.chain_id,
    )


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_deploy_account_hash", return_value=TX_HASH)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.transactions.get_class_hash", return_value=777)
async def test_deploy_account_get_tx_hash(
    mock_get_class_hash, mock_get_contract_class, mock_get_deploy_account_hash
):
    tx = DeployAccountTransaction()

    # Assert call for tx_hash
    mock_get_deploy_account_hash.assert_any_call(
        tx.predicted_address,
        tx.class_hash,
        tx.calldata,
        tx.salt,
        tx.max_fee,
        tx.nonce,
        TRANSACTION_VERSION,
        tx.chain_id,
    )

    # Assert call for query_hash
    mock_get_deploy_account_hash.assert_any_call(
        tx.predicted_address,
        tx.class_hash,
        tx.calldata,
        tx.salt,
        tx.max_fee,
        tx.nonce,
        QUERY_VERSION_BASE + TRANSACTION_VERSION,
        tx.chain_id,
    )


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_invoke_hash", return_value=TX_HASH)
async def test_invoke_get_execute_call_args(mock_get_invoke_hash):
    tx = InvokeTransaction()

    result = tx._get_execute_call_args()

    assert result == {
        "inputs": tx.calldata,
        "address": hex_address(tx.account_address),
        "abi": f"{NILE_ABIS_DIR}/Account.json",
        "method": tx.entry_point,
    }


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_declare_hash", return_value=TX_HASH)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
async def test_declare_get_execute_call_args(
    mock_get_contract_class, mock_get_declare_hash
):
    tx = DeclareTransaction()

    result = tx._get_execute_call_args()

    assert result == {
        "contract_name": tx.contract_to_submit,
        "overriding_path": tx.overriding_path,
        "sender": hex_address(tx.account_address),
    }


@pytest.mark.asyncio
@patch("nile.core.types.transactions.get_deploy_account_hash", return_value=TX_HASH)
@patch("nile.core.types.transactions.get_contract_class", return_value="ContractClass")
@patch("nile.core.types.transactions.get_class_hash", return_value=777)
async def test_deploy_account_get_execute_call_args(
    mock_get_class_hash, mock_get_contract_class, mock_get_deploy_account_hash
):
    tx = DeployAccountTransaction()

    result = tx._get_execute_call_args()

    assert result == {
        "salt": tx.salt,
        "contract_name": tx.contract_to_submit,
        "overriding_path": tx.overriding_path,
        "calldata": tx.calldata,
    }
