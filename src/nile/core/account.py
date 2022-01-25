"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import GATEWAYS
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
        params = [target_address, method] + list(calldata)
        _, abi = next(deployments.load(f"account-{self.index}", self.network))

        command = [
            "starknet",
            "invoke",
            "--address",
            self.address,
            "--abi",
            abi,
            "--function",
            "execute",
        ]

        if self.network == "mainnet":
            os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
        elif self.network == "goerli":
            os.environ["STARKNET_NETWORK"] = "alpha-goerli"
        else:
            gateway_prefix = "feeder_gateway" if type == "call" else "gateway"
            command.append(f"--{gateway_prefix}_url={GATEWAYS.get(self.network)}")

        if len(params) > 0:
            command.append("--inputs")
            nonce = self.get_nonce()
            ingested_inputs = self.signer.build_transaction(
                sender=self.address,
                to=params[0],
                selector=params[1],
                calldata=params[2:],
                nonce=nonce,
            )
            command.extend([str(param) for param in ingested_inputs[0]])
            command.append("--signature")
            command.extend([str(sig_part) for sig_part in ingested_inputs[1]])

        subprocess.check_call(command)

    def get_nonce(self):
        """Get the nonce for the next transaction."""
        nonce = subprocess.check_output(
            f"nile call account-{self.index} get_nonce --network {self.network}",
            shell=True,
            encoding="utf-8",
        )
        return int(nonce)
