"""Account module."""

import logging
import os

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import (
    NILE_ARTIFACTS_PATH,
    UNIVERSAL_DEPLOYER_ADDRESS,
    is_alias,
    normalize_number,
)
from nile.core.types.transactions import (
    DeclareTransaction,
    DeployAccountTransaction,
    InvokeTransaction,
)
from nile.core.types.tx_wrappers import (
    DeclareTxWrapper,
    DeployAccountTxWrapper,
    DeployContractTxWrapper,
    InvokeTxWrapper,
)
from nile.core.types.udc_helpers import create_udc_deploy_transaction
from nile.core.types.utils import get_counterfactual_address, get_execute_calldata
from nile.signer import Signer
from nile.utils.get_nonce import get_nonce_without_log as get_nonce

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
        auto_deploy=True,
    ):
        """Get or deploy an Account contract for the given private key."""
        signer, alias = _get_signer_and_alias(signer, predeployed_info)

        self.signer = signer
        self.alias = alias
        self.network = network

        if predeployed_info is not None:
            self.address = predeployed_info["address"]
            self.index = predeployed_info["index"]
        elif accounts.exists(self.signer.public_key, network):
            signer_data = next(accounts.load(self.signer.public_key, network))
            self.address = signer_data["address"]
            self.index = signer_data["index"]
        elif auto_deploy:
            tx = await self.deploy(salt=salt, max_fee=max_fee)
            # DeployAccountTxWrapper.execute updates account's address and index
            await tx.execute(watch_mode=watch_mode)

        # We should replace this with static type checks
        if hasattr(self, "address"):
            assert type(self.address) == int

    async def deploy(self, salt=None, max_fee=None, abi=None):
        """Deploy an Account contract for the given private key."""
        salt = 0 if salt is None else normalize_number(salt)
        calldata = [self.signer.public_key]
        contract_name = "Account"
        predicted_address = get_counterfactual_address(salt, calldata)

        max_fee, _, calldata = await self._process_arguments(max_fee, 0, calldata)

        # Create the transaction
        transaction = DeployAccountTransaction(
            salt=salt,
            contract_to_submit=contract_name,
            predicted_address=predicted_address,
            overriding_path=NILE_ARTIFACTS_PATH,
            calldata=calldata,
            max_fee=max_fee or 0,
            network=self.network,
        )

        tx_wrapper = DeployAccountTxWrapper(
            tx=transaction,
            account=self,
            alias=self.alias,
            abi=abi,
        )

        await _set_estimated_fee_if_none(max_fee, tx_wrapper)
        return tx_wrapper

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
            max_fee=max_fee or 0,
            nonce=nonce,
            network=self.network,
        )

        tx_wrapper = InvokeTxWrapper(
            tx=transaction,
            account=self,
        )

        await _set_estimated_fee_if_none(max_fee, tx_wrapper)
        return tx_wrapper

    async def declare(
        self,
        contract_name,
        nonce=None,
        max_fee=None,
        alias=None,
        overriding_path=None,
        nile_account=False,
    ):
        """Return a DeclareTxWrapper for declaring a contract through an Account."""
        max_fee, nonce, _ = await self._process_arguments(max_fee, nonce)

        if nile_account:
            assert overriding_path is None, "Cannot override path to Nile account."
            overriding_path = NILE_ARTIFACTS_PATH

        # Create the transaction
        transaction = DeclareTransaction(
            account_address=self.address,
            contract_to_submit=contract_name,
            max_fee=max_fee or 0,
            nonce=nonce,
            network=self.network,
            overriding_path=overriding_path,
        )

        tx_wrapper = DeclareTxWrapper(
            tx=transaction,
            account=self,
            alias=alias,
        )

        await _set_estimated_fee_if_none(max_fee, tx_wrapper)
        return tx_wrapper

    async def deploy_contract(
        self,
        contract_name,
        salt,
        unique,
        calldata,
        nonce=None,
        max_fee=None,
        deployer_address=None,
        alias=None,
        overriding_path=None,
        abi=None,
    ):
        """Deploy a contract through an Account."""
        deployer_address = normalize_number(
            deployer_address or UNIVERSAL_DEPLOYER_ADDRESS
        )
        max_fee, nonce, calldata = await self._process_arguments(
            max_fee, nonce, calldata
        )

        # Create the transaction
        transaction, predicted_address = await create_udc_deploy_transaction(
            account=self,
            contract_name=contract_name,
            salt=salt,
            unique=unique,
            calldata=calldata,
            deployer_address=deployer_address,
            max_fee=max_fee or 0,
            nonce=nonce,
            overriding_path=overriding_path,
        )

        tx_wrapper = DeployContractTxWrapper(
            tx=transaction,
            account=self,
            alias=alias,
            contract_name=contract_name,
            predicted_address=predicted_address,
            overriding_path=overriding_path,
            abi=abi,
        )

        await _set_estimated_fee_if_none(max_fee, tx_wrapper)
        return tx_wrapper

    def _get_target_address(self, address_or_alias):
        if not is_alias(address_or_alias):
            target_address = normalize_number(address_or_alias)
        else:
            target_address, _ = next(
                deployments.load(address_or_alias, self.network), None
            ) or (None, None)

            if type(target_address) != int:
                raise Exception(f"`{address_or_alias}` alias not found in deployments.")

        return target_address

    async def _process_arguments(self, max_fee, nonce, calldata=None):
        if max_fee is not None:
            max_fee = int(max_fee)

        if nonce is None:
            nonce = await get_nonce(self.address, self.network)

        if calldata is not None:
            calldata = [normalize_number(x) for x in calldata]

        return max_fee, nonce, calldata


def _get_signer_and_alias(signer, predeployed_info):
    if predeployed_info is None:
        alias = signer
        signer = Signer(normalize_number(os.environ[signer]))
    else:
        signer = Signer(signer)
        alias = predeployed_info["alias"]

    return signer, alias


async def _set_estimated_fee_if_none(max_fee, tx):
    """Estimate max_fee for transaction if max_fee is None."""
    if max_fee is None:
        logger = logging.getLogger()
        current_level = logger.level

        # Avoid logging the fee estimation in CLI
        logger.setLevel(logging.WARNING)

        estimated_fee = await tx.estimate_fee()

        logger.setLevel(current_level)

        tx.update_fee(estimated_fee)


async def try_get_account(
    signer,
    network,
    salt=None,
    max_fee=None,
    predeployed_info=None,
    watch_mode=None,
    auto_deploy=True,
):
    """Avoid reverting on KeyError."""
    account = None
    try:
        account = await Account(
            signer,
            network,
            salt=salt,
            max_fee=max_fee,
            predeployed_info=predeployed_info,
            watch_mode=watch_mode,
            auto_deploy=auto_deploy,
        )
    except KeyError:
        logging.error(
            f"\n❌ Cannot find {signer} in env."
            "\nCheck spelling and that it exists."
            "\nTry moving the .env to the root of your project."
        )

    return account
