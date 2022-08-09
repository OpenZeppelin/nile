"""
Tests for signer.py.

A high-level synchronization check between the Account artifacts and Signer module.
"""

import asyncio

import pytest
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.testing.starknet import Starknet

from nile.signer import Signer

SIGNER = Signer(12345678987654321)


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
    if nonce is None:
        execution_info = await account.get_nonce().call()
        (nonce,) = execution_info.result

    build_calls = []
    for call in calls:
        build_call = list(call)
        build_call[0] = hex(build_call[0])
        build_calls.append(build_call)

    (call_array, calldata, sig_r, sig_s) = signer.sign_transaction(
        hex(account.contract_address), build_calls, nonce, max_fee
    )
    return await account.__execute__(call_array, calldata, nonce).invoke(
        signature=[sig_r, sig_s]
    )


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
    await send_transaction(
        SIGNER, account, contract.contract_address, "increase_balance", [1]
    )
    execution_info = await contract.get_balance().call()
    assert execution_info.result == (1,)

    # Multicall tx
    await send_transactions(
        SIGNER,
        account,
        [
            (contract.contract_address, "increase_balance", [1]),
            (contract.contract_address, "increase_balance", [1]),
        ],
    )
    execution_info = await contract.get_balance().call()
    assert execution_info.result == (3,)
