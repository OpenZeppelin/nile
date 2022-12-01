"""Utils for handling types logic."""

from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)
from starkware.starknet.core.os.transaction_hash.transaction_hash import (
    TransactionHashPrefix,
    calculate_declare_transaction_hash,
    calculate_deploy_account_transaction_hash,
    calculate_transaction_hash_common,
)
from starkware.starknet.public.abi import get_selector_from_name

from nile.common import get_account_class_hash


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
        tx_hash_prefix=TransactionHashPrefix.INVOKE,
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


def get_counterfactual_address(salt=None, calldata=None, contract="Account"):
    """Precompute a contract's address for a given class, salt, and calldata."""
    class_hash = get_account_class_hash(contract)
    salt = 0 if salt is None else int(salt)
    calldata = [] if calldata is None else calldata
    return calculate_contract_address_from_hash(
        salt=salt,
        class_hash=class_hash,
        constructor_calldata=calldata,
        deployer_address=0,
    )
