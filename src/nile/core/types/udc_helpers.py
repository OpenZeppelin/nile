"""Wrappers for UDC transactions."""

from starkware.cairo.common.hash_chain import compute_hash_chain
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile.common import get_class_hash
from nile.core.types.transactions import InvokeTransaction
from nile.core.types.utils import get_execute_calldata


async def create_udc_deploy_transaction(
    account,
    contract_name: str,
    salt: int,
    unique: bool,
    calldata,
    deployer_address: int,
    max_fee: int,
    nonce: int = None,
    overriding_path=None,
):
    """Return a transaction representing a UDC deployment."""
    deployer_for_address_generation = 0

    if salt is None:
        salt = 0

    _salt = salt
    if unique:
        _salt = compute_hash_chain(data=[account.address, salt])
        deployer_for_address_generation = deployer_address

    max_fee, nonce, calldata = await account._process_arguments(
        max_fee, nonce, calldata
    )
    class_hash = get_class_hash(contract_name, overriding_path)

    execute_calldata = get_execute_calldata(
        calls=[
            [
                deployer_address,
                "deployContract",
                [class_hash, salt, 1 if unique else 0, len(calldata), *calldata],
            ]
        ]
    )

    tx = InvokeTransaction(
        account_address=account.address,
        calldata=execute_calldata,
        max_fee=max_fee,
        nonce=nonce,
        network=account.network,
    )

    predicted_address = calculate_contract_address_from_hash(
        _salt, class_hash, calldata, deployer_for_address_generation
    )

    return tx, predicted_address
