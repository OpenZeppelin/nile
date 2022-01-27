"""Utility for sending signed transactions to an Account on Starknet."""
try:
    from starkware.cairo.common.hash_state import compute_hash_on_elements
    from starkware.crypto.signature.signature import private_to_stark_key, sign
    from starkware.starknet.public.abi import get_selector_from_name

    starkware_found = True
except ImportError:
    starkware_found = False


class Signer:
    """Utility for sending signed transactions to an Account on Starknet."""

    def __init__(self, private_key):
        """Construct a Signer object. Takes a private key."""
        if not starkware_found:
            raise Exception("starkware module not found")
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)

    def sign(self, message_hash):
        """Sign a message hash."""
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    def sign_message(self, sender, to, selector, calldata, nonce):
        """Get the inputs for the next transaction in a CLI context."""
        selector = get_selector_from_name(selector)
        ingested_calldata = [int(arg, 16) for arg in calldata]
        message_hash = hash_message(
            int(sender, 16), int(to, 16), selector, ingested_calldata, nonce
        )
        sig_r, sig_s = self.sign(message_hash)
        return (
            (int(to, 16), selector, len(ingested_calldata), *ingested_calldata, nonce),
            (sig_r, sig_s),
        )


def hash_message(sender, to, selector, calldata, nonce):
    """Hash a message."""
    message = [sender, to, selector, compute_hash_on_elements(calldata), nonce]
    return compute_hash_on_elements(message)
