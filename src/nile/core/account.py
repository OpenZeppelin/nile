"""Command to call or invoke StarkNet smart contracts."""
import os

from dotenv import load_dotenv

from nile import accounts, deployments
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
        self.signer = Signer(int(os.environ[signer]))
        self.network = network

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

        accounts.register(self.signer.public_key, address, index, self.network)

        return address, index

    def send(self, to, method, calldata, max_fee, nonce=None):
        """Execute a tx going through an Account contract."""
        target_address, _ = next(deployments.load(to, self.network)) or to
        calldata = [int(x) for x in calldata]

        if nonce is None:
            nonce = int(
                call_or_invoke(self.address, "call", "get_nonce", [], self.network)
            )

        if max_fee is None:
            max_fee = 0

        (call_array, calldata, sig_r, sig_s) = self.signer.sign_transaction(
            sender=self.address,
            calls=[[target_address, method, calldata]],
            nonce=nonce,
            max_fee=max_fee,
        )

        params = []
        params.append(str(len(call_array)))
        params.extend([str(elem) for sublist in call_array for elem in sublist])
        params.append(str(len(calldata)))
        params.extend([str(param) for param in calldata])
        params.append(str(nonce))

        return call_or_invoke(
            contract=self.address,
            type="invoke",
            method="__execute__",
            params=params,
            network=self.network,
            signature=[str(sig_r), str(sig_s)],
            max_fee=str(max_fee),
        )
