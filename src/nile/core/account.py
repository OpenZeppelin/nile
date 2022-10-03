"""Command to call or invoke StarkNet smart contracts."""
import logging
import os

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import is_alias
from nile.core.call_or_invoke import call_or_invoke
from nile.core.deploy import deploy
from nile.utils import normalize_number
from nile.utils.get_nonce import get_nonce_without_log as get_nonce

try:
    from nile.signer import Signer
except ImportError:
    pass

load_dotenv()


class Account:
    """Account contract abstraction."""

    def __init__(self, signer, network, predeployed_info=None):
        """Get or deploy an Account contract for the given private key."""
        try:
            if predeployed_info is None:
                self.signer = Signer(normalize_number(os.environ[signer]))
                self.alias = signer
            else:
                self.signer = Signer(signer)
                self.alias = predeployed_info["alias"]

            self.network = network
        except KeyError:
            logging.error(
                f"\n❌ Cannot find {signer} in env."
                "\nCheck spelling and that it exists."
                "\nTry moving the .env to the root of your project."
            )
            return

        self.abi_path = os.path.dirname(os.path.realpath(__file__)).replace(
            "/core", "/artifacts/abis/Account.json"
        )

        if predeployed_info is not None:
            self.address = predeployed_info["address"]
            self.index = predeployed_info["index"]
        elif accounts.exists(self.signer.public_key, network):
            signer_data = next(accounts.load(self.signer.public_key, network))
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
            [self.signer.public_key],
            self.network,
            f"account-{index}",
            overriding_path,
        )

        accounts.register(
            self.signer.public_key, address, index, self.alias, self.network
        )

        return address, index

    def send(self, address_or_alias, method, calldata, max_fee, nonce=None):
        """Execute a tx going through an Account contract."""
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)

        target_address, _ = (
            next(deployments.load(address_or_alias, self.network), None)
            or address_or_alias
        )

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
            contract=self,
            type="invoke",
            method="__execute__",
            params=calldata,
            network=self.network,
            signature=[str(sig_r), str(sig_s)],
            max_fee=str(max_fee),
        )
