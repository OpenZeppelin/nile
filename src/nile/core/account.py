"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.core.call_or_invoke import call_or_invoke
from nile.core.deploy import deploy
from nile.signer import Signer

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

    def send(self, to, method, calldata):
        """Execute a tx going through an Account contract."""
        target_address, _ = next(deployments.load(to, self.network)) or to

        message, signature = self.signer.sign_message(
            sender=self.address,
            to=target_address,
            selector=method,
            calldata=calldata,
            nonce=self.get_nonce(),
        )

        call_or_invoke(
            contract=self.address,
            type="invoke",
            method="execute",
            params=message,
            network=self.network,
            signature=signature,
        )

    def get_nonce(self):
        """Get the nonce for the next transaction."""
        nonce = subprocess.check_output(
            f"nile call account-{self.index} get_nonce --network {self.network}",
            shell=True,
            encoding="utf-8",
        )
        return int(nonce)
