"""Utility for signing transactions for an Account on Starknet."""

from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.starknet.core.os.transaction_hash.transaction_hash import (
    TransactionHashPrefix,
    calculate_declare_transaction_hash,
    calculate_transaction_hash_common,
)
from starkware.starknet.definitions.general_config import StarknetChainId
from starkware.starknet.public.abi import get_selector_from_name

from nile.common import TRANSACTION_VERSION


class Signer:
    """Utility for signing transactions for an Account on Starknet."""

    def __init__(self, private_key):
        """Construct a Signer object. Takes a private key."""
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)

    def sign(self, message_hash):
        """Sign a message hash."""
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    def sign_declare(self, sender, contract_class, nonce, max_fee):
        """Sign a declare transaction."""
        if isinstance(sender, str):
            sender = int(sender, 16)

        transaction_hash = get_declare_hash(
            sender=sender,
            contract_class=contract_class,
            max_fee=max_fee,
            nonce=nonce,
        )

        return self.sign(message_hash=transaction_hash)

    def sign_transaction(
        self, sender, calls, nonce, max_fee, version=TRANSACTION_VERSION
    ):
        """Sign a transaction."""
        call_array, calldata = from_call_to_call_array(calls)
        execute_calldata = [
            len(call_array),
            *[x for t in call_array for x in t],
            len(calldata),
            *calldata,
        ]

        if isinstance(sender, str):
            sender = int(sender, 16)

        transaction_hash = get_transaction_hash(
            prefix=TransactionHashPrefix.INVOKE,
            account=sender,
            calldata=execute_calldata,
            nonce=nonce,
            max_fee=max_fee,
            version=version,
        )

        sig_r, sig_s = self.sign(message_hash=transaction_hash)
        return execute_calldata, sig_r, sig_s


# Auxiliary functions


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


def get_declare_hash(sender, contract_class, max_fee, nonce):
    """Compute the hash of a declare transaction."""
    return calculate_declare_transaction_hash(
        contract_class=contract_class,
        chain_id=StarknetChainId.TESTNET.value,
        sender_address=sender,
        max_fee=max_fee,
        version=TRANSACTION_VERSION,
        nonce=nonce,
    )


def get_transaction_hash(prefix, account, calldata, nonce, max_fee, version):
    """Compute the hash of a transaction."""
    return calculate_transaction_hash_common(
        tx_hash_prefix=prefix,
        version=version,
        contract_address=account,
        entry_point_selector=0,
        calldata=calldata,
        max_fee=max_fee,
        chain_id=StarknetChainId.TESTNET.value,
        additional_data=[nonce],
    )
