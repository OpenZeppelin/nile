"""Account module."""
import logging
import os

from dotenv import load_dotenv
from starkware.starknet.definitions.general_config import StarknetChainId

from nile import accounts, deployments
from nile.common import (
    TRANSACTION_VERSION,
    UNIVERSAL_DEPLOYER_ADDRESS,
    get_account_class_hash,
    is_alias,
    normalize_number,
)
from nile.core.deploy import deploy_account
from nile.core.types.account_tx_wrappers import (
    DeclareTxWrapper,
    DeployContractTxWrapper,
    InvokeTxWrapper,
)
from nile.core.types.transactions import DeclareTransaction, InvokeTransaction
from nile.core.types.udc_helpers import create_udc_deploy_transaction
from nile.core.types.utils import (
    get_counterfactual_address,
    get_deploy_account_hash,
    get_execute_calldata,
)
from nile.utils.get_nonce import get_nonce_without_log as get_nonce

try:
    from nile.core.types.signer import Signer
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

    async def __init__(
        self,
        signer,
        network,
        salt=0,
        max_fee=None,
        predeployed_info=None,
        watch_mode=None,
    ):
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
            output = await self.deploy(
                salt=salt, max_fee=max_fee, watch_mode=watch_mode
            )
            if output is not None:
                address, index = output
                self.address = normalize_number(address)
                self.index = index

        # we should replace this with static type checks
        if hasattr(self, "address"):
            assert type(self.address) == int

    async def deploy(self, salt=None, max_fee=None, query_type=None, watch_mode=None):
        """Deploy an Account contract for the given private key."""
        index = accounts.current_index(self.network)
        pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
        overriding_path = (f"{pt}/artifacts", f"{pt}/artifacts/abis")

        class_hash = get_account_class_hash("Account")
        salt = 0 if salt is None else normalize_number(salt)
        max_fee = 0 if max_fee is None else normalize_number(max_fee)
        calldata = [self.signer.public_key]

        contract_address = get_counterfactual_address(salt, calldata)

        chain_id = (
            StarknetChainId.MAINNET.value
            if self.network == "mainnet"
            else StarknetChainId.TESTNET.value
        )

        tx_hash = get_deploy_account_hash(
            contract_address,
            class_hash,
            calldata,
            salt,
            max_fee,
            0,  # nonce starts at 0
            TRANSACTION_VERSION,
            chain_id,
        )

        [sig_r, sig_s] = self.signer.sign(tx_hash)

        output = await deploy_account(
            network=self.network,
            salt=salt,
            calldata=calldata,
            signature=[sig_r, sig_s],
            max_fee=max_fee,
            query_type=query_type,
            overriding_path=overriding_path,
            watch_mode=watch_mode,
        )

        if output is not None:
            address, *_ = output
            accounts.register(
                self.signer.public_key, address, index, self.alias, self.network
            )
            return address, index

    async def send(
        self,
        address_or_alias,
        method,
        calldata,
        nonce=None,
        max_fee=None,
    ):
        """Return an InvokeTxWrapper object."""
        target_address = self._get_target_address(address_or_alias)
        max_fee, nonce, calldata = await self._process_arguments(
            max_fee, nonce, calldata
        )
        execute_calldata = get_execute_calldata(
            calls=[[target_address, method, calldata]]
        )

        # Create the transaction
        transaction = InvokeTransaction(
            account_address=self.address,
            calldata=execute_calldata,
            max_fee=max_fee,
            nonce=nonce,
            network=self.network,
        )

        return InvokeTxWrapper(
            tx=transaction,
            account=self,
        )

    async def declare(
        self,
        contract_name,
        max_fee=None,
        nonce=None,
        alias=None,
        overriding_path=None,
        mainnet_token=None,
    ):
        """Return a DeclareTxWrapper for declaring a contract through an Account."""
        max_fee, nonce, _ = await self._process_arguments(max_fee, nonce)

        # Create the transaction
        transaction = DeclareTransaction(
            account_address=self.address,
            contract_to_submit=contract_name,
            max_fee=max_fee,
            nonce=nonce,
            network=self.network,
        )

        return DeclareTxWrapper(
            tx=transaction,
            account=self,
            alias=alias,
            overriding_path=overriding_path,
            mainnet_token=mainnet_token,
        )

    async def deploy_contract(
        self,
        contract_name,
        salt,
        unique,
        calldata,
        alias,
        max_fee=None,
        deployer_address=None,
        overriding_path=None,
        abi=None,
    ):
        """Deploy a contract through an Account."""
        deployer_address = normalize_number(
            deployer_address or UNIVERSAL_DEPLOYER_ADDRESS
        )

        # Create the transaction
        transaction = await create_udc_deploy_transaction(
            account=self,
            contract_name=contract_name,
            salt=salt,
            unique=unique,
            calldata=calldata,
            deployer_address=deployer_address,
            max_fee=max_fee,
            overriding_path=overriding_path,
        )

        return DeployContractTxWrapper(
            tx=transaction,
            account=self,
            alias=alias,
            overriding_path=overriding_path,
        )

    def _get_target_address(self, address_or_alias):
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)

        target_address, _ = next(
            deployments.load(address_or_alias, self.network), None
        ) or (address_or_alias, None)

        return target_address

    async def _process_arguments(self, max_fee, nonce, calldata=None):
        max_fee = 0 if max_fee is None else int(max_fee)

        if nonce is None:
            nonce = await get_nonce(self.address, self.network)

        if calldata is not None:
            calldata = [normalize_number(x) for x in calldata]

        return max_fee, nonce, calldata
