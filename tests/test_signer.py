"""
Tests for signer.py.

A high-level synchronization check between the Account artifacts and Signer module.
"""

import asyncio

import pytest
from starkware.starknet.business_logic.transaction.objects import InternalTransaction
from starkware.starknet.definitions.general_config import StarknetChainId
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.services.api.gateway.transaction import InvokeFunction
from starkware.starknet.testing.starknet import Starknet

from nile.common import TRANSACTION_VERSION
from nile.signer import Signer, from_call_to_call_array

PRIVATE_KEY = 12345678987654321
SIGNER = Signer(PRIVATE_KEY)


def get_account_definition():
    with open("src/nile/artifacts/Account.json", "r") as fp:
        return ContractClass.loads(fp.read())


async def send_transaction(
    signer, account, to, selector_name, calldata, nonce=None, max_fee=0
):
    return await send_transactions(
        signer, account, [(to, selector_name, calldata)], nonce, max_fee
    )


async def send_transactions(signer, account, calls, nonce=None, max_fee=0):
    # hexify address before passing to from_call_to_call_array
    raw_invocation = get_raw_invoke(account, calls)
    state = raw_invocation.state

    if nonce is None:
        nonce = await state.state.get_nonce_at(account.contract_address)

    # get signature
    calldata, sig_r, sig_s = signer.sign_invoke(
        account.contract_address, calls, nonce, max_fee, TRANSACTION_VERSION
    )

    # craft invoke and execute tx
    external_tx = InvokeFunction(
        contract_address=account.contract_address,
        calldata=calldata,
        entry_point_selector=None,
        signature=[sig_r, sig_s],
        max_fee=max_fee,
        version=TRANSACTION_VERSION,
        nonce=nonce,
    )

    tx = InternalTransaction.from_external(
        external_tx=external_tx, general_config=state.general_config
    )
    execution_info = await state.execute_tx(tx=tx)
    return execution_info


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()


@pytest.mark.asyncio
async def test_execute():
    starknet = await Starknet.empty()
    account = await starknet.deploy(
        contract_class=get_account_definition(),
        constructor_calldata=[SIGNER.public_key],
    )
    contract = await starknet.deploy(
        "tests/resources/contracts/contract.cairo",
    )

    # Ensures balance is zero
    execution_info = await contract.get_balance().call()
    assert execution_info.result == (0,)

    # Single tx
    nonce = await starknet.state.state.get_nonce_at(account.contract_address)
    await send_transaction(
        SIGNER, account, contract.contract_address, "increase_balance", [1], nonce
    )

    execution_info = await contract.get_balance().call()
    assert execution_info.result == (1,)

    # Multicall tx
    nonce = await starknet.state.state.get_nonce_at(account.contract_address)
    await send_transactions(
        SIGNER,
        account,
        [
            (contract.contract_address, "increase_balance", [1]),
            (contract.contract_address, "increase_balance", [1]),
        ],
        nonce,
    )
    execution_info = await contract.get_balance().call()
    assert execution_info.result == (3,)


@pytest.mark.asyncio
async def test_chain_id():
    mainnet = Signer(PRIVATE_KEY, "mainnet")
    assert mainnet.chain_id == StarknetChainId.MAINNET.value

    testnet = Signer(PRIVATE_KEY, "testnet")
    assert testnet.chain_id == StarknetChainId.TESTNET.value

    no_network = Signer(PRIVATE_KEY)
    assert no_network.chain_id == StarknetChainId.TESTNET.value


def get_raw_invoke(sender, calls):
    """Construct and return StarkNet's internal raw_invocation."""
    call_array, calldata = from_call_to_call_array(calls)
    raw_invocation = sender.__execute__(call_array, calldata)
    return raw_invocation
