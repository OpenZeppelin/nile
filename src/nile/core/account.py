"""Command to call or invoke StarkNet smart contracts."""
import logging
import os

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import (
    QUERY_VERSION,
    TRANSACTION_VERSION,
    UNIVERSAL_DEPLOYER_ADDRESS,
    get_contract_class,
    is_alias,
    normalize_number,
)
from nile.core.call_or_invoke import call_or_invoke
from nile.core.declare import declare
from nile.core.deploy import deploy
from nile.utils.get_nonce import get_nonce_without_log as get_nonce

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
    """
    Account contract abstraction.

    Remove AsyncObject if Account.deploy decouples from initialization.
    """

    async def __init__(self, signer, network, predeployed_info=None, watch_mode=None):
        """Get or deploy an Account contract for the given private key."""
        try:
            if predeployed_info is None:
                self.signer = Signer(normalize_number(os.environ[signer]), network)
                self.alias = signer
            else:
                self.signer = Signer(signer, network)
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
            address, index = await self.deploy(watch_mode=watch_mode)
            self.address = address
            self.index = index

    async def deploy(self, watch_mode=None):
        """Deploy an Account contract for the given private key."""
        index = accounts.current_index(self.network)
        pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
        overriding_path = (f"{pt}/artifacts", f"{pt}/artifacts/abis")

        address, _ = await deploy(
            "Account",
            [self.signer.public_key],
            self.network,
            f"account-{index}",
            overriding_path,
            watch_mode=watch_mode,
        )

        accounts.register(
            self.signer.public_key, address, index, self.alias, self.network
        )

        return address, index

    async def declare(
        self,
        contract_name,
        max_fee=None,
        nonce=None,
        alias=None,
        overriding_path=None,
        mainnet_token=None,
        watch_mode=None,
    ):
        """Declare a contract through an Account contract."""
        max_fee, nonce, _ = await self._process_arguments(max_fee, nonce)

        contract_class = get_contract_class(
            contract_name=contract_name, overriding_path=overriding_path
        )

        sig_r, sig_s = self.signer.sign_declare(
            sender=self.address,
            contract_class=contract_class,
            nonce=nonce,
            max_fee=max_fee,
        )

        return await declare(
            sender=self.address,
            contract_name=contract_name,
            signature=[sig_r, sig_s],
            alias=alias,
            network=self.network,
            max_fee=max_fee,
            mainnet_token=mainnet_token,
            watch_mode=watch_mode,
        )

    async def deploy_contract(
        self,
        class_hash,
        salt,
        unique,
        calldata,
        max_fee=None,
        deployer_address=None,
        watch_mode=None,
    ):
        """Deploy a contract through an Account contract."""
        return await self.send(
            to=deployer_address or UNIVERSAL_DEPLOYER_ADDRESS,
            method="deployContract",
            calldata=[class_hash, salt, unique, len(calldata), *calldata],
            max_fee=max_fee,
            watch_mode=watch_mode,
        )

    async def send(
        self,
        address_or_alias,
        method,
        calldata,
        nonce=None,
        max_fee=None,
        query_type=None,
        watch_mode=None,
    ):
        """Execute a query or invoke call for a tx going through an Account contract."""
        # get target address with the right format
        target_address = self._get_target_address(address_or_alias)

        # process and parse arguments
        max_fee, nonce, calldata = await self._process_arguments(
            max_fee, nonce, calldata
        )

        # get tx version
        tx_version = QUERY_VERSION if query_type else TRANSACTION_VERSION

        calldata, sig_r, sig_s = self.signer.sign_transaction(
            sender=self.address,
            calls=[[target_address, method, calldata]],
            nonce=nonce,
            max_fee=max_fee,
            version=tx_version,
        )

        return await call_or_invoke(
            contract=self,
            type="invoke",
            method="__execute__",
            params=calldata,
            network=self.network,
            signature=[str(sig_r), str(sig_s)],
            max_fee=str(max_fee),
            query_flag=query_type,
            watch_mode=watch_mode,
        )

    def simulate(self, address_or_alias, method, calldata, max_fee=None, nonce=None):
        """Simulate a tx going through an Account contract."""
        return self.send(address_or_alias, method, calldata, max_fee, nonce, "simulate")

    def estimate_fee(
        self, address_or_alias, method, calldata, max_fee=None, nonce=None
    ):
        """Estimate fee for a tx going through an Account contract."""
        return self.send(
            address_or_alias, method, calldata, max_fee, nonce, "estimate_fee"
        )

    def _get_target_address(self, address_or_alias):
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)

        target_address, _ = (
            next(deployments.load(address_or_alias, self.network), None)
            or address_or_alias
        )

        return target_address

    async def _process_arguments(self, max_fee, nonce, calldata=None):
        max_fee = 0 if max_fee is None else int(max_fee)

        if nonce is None:
            nonce = await get_nonce(self.address, self.network)

        if calldata is not None:
            calldata = [normalize_number(x) for x in calldata]

        return max_fee, nonce, calldata
