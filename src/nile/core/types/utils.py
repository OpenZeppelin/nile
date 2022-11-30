"""Utils for handling types logic."""

from starkware.starknet.core.os.transaction_hash.transaction_hash import (
    TransactionHashPrefix,
    calculate_declare_transaction_hash,
    calculate_deploy_account_transaction_hash,
    calculate_transaction_hash_common,
)
from starkware.starknet.public.abi import get_selector_from_name


def get_execute_calldata(calls):
    """Generate __execute__ format calldata from calls."""
    call_array, calldata = from_call_to_call_array(calls)
    execute_calldata = [
        len(call_array),
        *[x for t in call_array for x in t],
        len(calldata),
        *calldata,
    ]

    return execute_calldata


def from_call_to_call_array(calls):
    """Transform from Call to CallArray."""
    call_array = []
    calldata = []
    for _, call in enumerate(calls):
        assert len(call) == 3, "Invalid call parameters"
        entry = (
            call[0],
            get_selector_from_name(call[1]),
            len(calldata),
            len(call[2]),
        )
        call_array.append(entry)
        calldata.extend(call[2])
    return (call_array, calldata)


def get_invoke_hash(account, calldata, max_fee, nonce, version, chain_id):
    """Compute the hash of an invoke transaction."""
    return calculate_transaction_hash_common(
        tx_hash_prefix=TransactionHashPrefix,
        version=version,
        contract_address=account,
        entry_point_selector=0,
        calldata=calldata,
        max_fee=max_fee,
        chain_id=chain_id,
        additional_data=[nonce],
    )


def get_declare_hash(account, contract_class, max_fee, nonce, version, chain_id):
    """Compute the hash of a declare transaction."""
    return calculate_declare_transaction_hash(
        version=version,
        sender_address=account,
        contract_class=contract_class,
        max_fee=max_fee,
        nonce=nonce,
        chain_id=chain_id,
    )


def get_deploy_account_hash(
    contract_address, class_hash, calldata, salt, max_fee, nonce, version, chain_id
):
    """Compute the hash of an account deployment transaction."""
    return calculate_deploy_account_transaction_hash(
        version=version,
        contract_address=contract_address,
        class_hash=class_hash,
        constructor_calldata=calldata,
        max_fee=max_fee,
        nonce=nonce,
        salt=salt,
        chain_id=chain_id,
    )
