"""Utility for signing transactions for an Account on Starknet."""

from starkware.crypto.signature.signature import private_to_stark_key, sign


class Signer:
    """Utility for signing transactions for an Account on Starknet."""

    def __init__(self, private_key):
        """Construct a Signer object. Takes a private key."""
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)

    def sign(self, message_hash):
        """Sign a message hash."""
        return sign(msg_hash=message_hash, priv_key=self.private_key)
