"""Utility for signing transactions for an Account on Starknet."""

from starkware.crypto.signature.signature import private_to_stark_key, sign

from nile.common import TRANSACTION_VERSION, get_chain_id
from nile.core.types.utils import (
    get_declare_hash,
    get_deploy_account_hash,
    get_execute_calldata,
    get_invoke_hash,
)


class Signer:
    """Utility for signing transactions for an Account on Starknet."""

    def __init__(self, private_key, network="testnet"):
        """Construct a Signer object. Takes a private key."""
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)
        self.chain_id = get_chain_id(network)

    def sign(self, message_hash):
        """Sign a message hash."""
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    def sign_deployment(
        self, contract_address, class_hash, calldata, salt, max_fee, nonce
    ):
        """Sign a deploy_account transaction."""
        transaction_hash = get_deploy_account_hash(
            contract_address,
            class_hash,
            calldata,
            salt,
            max_fee,
            nonce,
            self.chain_id,
        )

        return self.sign(message_hash=transaction_hash)

    def sign_declare(self, sender, contract_class, nonce, max_fee):
        """Sign a declare transaction."""
        if isinstance(sender, str):
            sender = int(sender, 16)

        transaction_hash = get_declare_hash(
            sender=sender,
            contract_class=contract_class,
            max_fee=max_fee,
            nonce=nonce,
            chain_id=self.chain_id,
        )

        return self.sign(message_hash=transaction_hash)

    def sign_invoke(self, sender, calls, nonce, max_fee, version=TRANSACTION_VERSION):
        """Sign an invoke transaction."""
        execute_calldata = get_execute_calldata(calls)

        if isinstance(sender, str):
            sender = int(sender, 16)

        transaction_hash = get_invoke_hash(
            account=sender,
            calldata=execute_calldata,
            nonce=nonce,
            max_fee=max_fee,
            version=version,
            chain_id=self.chain_id,
        )

        sig_r, sig_s = self.sign(message_hash=transaction_hash)
        return execute_calldata, sig_r, sig_s
