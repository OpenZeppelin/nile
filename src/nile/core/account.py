"""Command to call or invoke StarkNet smart contracts."""
import logging
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


class AsyncObject(object):
    """Base class for Account to allow async initialization."""

    async def __new__(cls, *a, **kw):
        """Return coroutine (not class so sync __init__ is not invoked)."""
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        """Support Account async __init__."""
        pass


class Account(AsyncObject):
    """Account contract abstraction."""

    async def __init__(self, signer, network):
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

        if accounts.exists(str(self.signer.public_key), self.network):
            signer_data = next(accounts.load(str(self.signer.public_key), self.network))
            self.address = signer_data["address"]
            self.index = signer_data["index"]
        else:
            address, index = await self.deploy()
            self.address = address
            self.index = index

    async def deploy(self):
        """Deploy an Account contract for the given private key."""
        index = accounts.current_index(self.network)
        pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
        overriding_path = (f"{pt}/artifacts", f"{pt}/artifacts/abis")

        address, _ = await deploy(
            contract_name="Account",
            arguments=[str(self.signer.public_key)],
            network=self.network,
            alias=f"account-{index}",
            overriding_path=overriding_path,
        )

        accounts.register(self.signer.public_key, address, index, self.network)
        return address, index

    async def send(self, to, method, calldata, max_fee=None, nonce=None):
        """Execute a tx going through an Account contract."""
        target_address, _ = next(deployments.load(to, self.network)) or to
        calldata = [int(x) for x in calldata]

        if nonce is None:
            nonce = await self.get_nonce()

        if max_fee is None:
            max_fee = 0

        (call_array, calldata, sig_r, sig_s) = self.signer.sign_transaction(
            sender=self.address,
            calls=[[target_address, method, calldata]],
            nonce=nonce,
            max_fee=max_fee,
        )

        params = []
        params.append(len(call_array))
        params.extend(*call_array)
        params.append(len(calldata))
        params.extend(calldata)
        params.append(nonce)

        return await call_or_invoke(
            contract=self.address,
            type="invoke",
            method="__execute__",
            params=params,
            network=self.network,
            signature=[sig_r, sig_s],
            max_fee=max_fee,
        )

    async def get_nonce(self):
        """Return nonce from account contract."""
        return await call_or_invoke(
            contract=self.address,
            type="call",
            method="get_nonce",
            params=[],
            network=self.network,
        )
