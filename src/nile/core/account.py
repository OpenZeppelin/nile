"""Command to call or invoke StarkNet smart contracts."""
import logging
import os

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import get_nonce
from nile.core.call_or_invoke import call_or_invoke
from nile.core.deploy import deploy

try:
    from nile.signer import Signer
except ImportError:
    pass

load_dotenv()


class Account:
    """Account contract abstraction."""

    def __init__(self, signer, network):
        """Get or deploy an Account contract for the given private key."""
        try:
            self.signer = Signer(int(os.environ[signer]))
            self.alias = signer
            self.network = network
        except KeyError:
            logging.error(
                f"\n❌ Cannot find {signer} in env."
                "\nCheck spelling and that it exists."
                "\nTry moving the .env to the root of your project."
            )
            return

        if accounts.exists(str(self.signer.public_key), network):
            signer_data = next(accounts.load(str(self.signer.public_key), network))
            self.address = signer_data["address"]
            self.index = signer_data["index"]
        else:
            address, index = self.deploy()
            self.address = address
            self.index = index

    def deploy(self):
        """Deploy an Account contract for the given private key."""
        index = accounts.current_index(self.network)
        pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
        overriding_path = (f"{pt}/artifacts", f"{pt}/artifacts/abis")

        address, _ = deploy(
            "Account",
            [str(self.signer.public_key)],
            self.network,
            f"account-{index}",
            overriding_path,
        )

        accounts.register(
            self.signer.public_key, address, index, self.alias, self.network
        )

        return address, index

    def send(self, to, method, calldata, max_fee, nonce=None):
        """Execute a tx going through an Account contract."""
        target_address, _ = next(deployments.load(to, self.network)) or to
        calldata = [int(x) for x in calldata]

        if nonce is None:
            nonce = get_nonce(self.address, self.network)

        if max_fee is None:
            max_fee = 0
        else:
            max_fee = int(max_fee)

        calldata, sig_r, sig_s = self.signer.sign_transaction(
            sender=self.address,
            calls=[[target_address, method, calldata]],
            nonce=nonce,
            max_fee=max_fee,
        )

        return call_or_invoke(
            contract=self.address,
            type="invoke",
            method="__execute__",
            params=calldata,
            network=self.network,
            signature=[str(sig_r), str(sig_s)],
            max_fee=str(max_fee),
        )
