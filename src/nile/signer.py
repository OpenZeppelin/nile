"""Utility for sending signed transactions to an Account on Starknet."""
import subprocess

from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.starknet.public.abi import get_selector_from_name
from starkware.cairo.common.hash_state import compute_hash_on_elements

class Signer():
    """
    Utility for sending signed transactions to an Account on Starknet.

    Parameters
    ----------

    private_key : int

    Examples
    ---------
    Constructing a Singer object

    >>> signer = Signer(1234)

    Sending a transaction

    >>> await signer.send_transaction(account, 
                                      account.contract_address, 
                                      'set_public_key', 
                                      [other.public_key]
                                     )

    """

    def __init__(self, private_key):
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)
        self.account = None
        self.index = 0

    def sign(self, message_hash):
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    def get_nonce(self):
        nonce = subprocess.check_output(f"nile call account-{self.index} get_nonce", shell=True, encoding='utf-8')
        return int(nonce)

    def get_inputs(self, to, selector_name, calldata):
        nonce = self.get_nonce()
        selector = get_selector_from_name(selector_name)
        ingested_calldata = [int(arg, 16) for arg in calldata]
        message_hash = hash_message(int(self.account,16), int(to,16), selector, ingested_calldata, nonce)
        sig_r, sig_s = self.sign(message_hash)
        return ((int(to,16), selector, len(ingested_calldata), *ingested_calldata, nonce), (sig_r, sig_s))


def hash_message(sender, to, selector, calldata, nonce):
    message = [
        sender,
        to,
        selector,
        compute_hash_on_elements(calldata),
        nonce
    ]
    return compute_hash_on_elements(message)
