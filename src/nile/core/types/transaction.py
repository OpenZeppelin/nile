"""Transaction module."""

import dataclasses
import re
from dataclasses import field
from typing import List, Literal

from starkware.starknet.definitions.general_config import StarknetChainId
from starkware.starknet.public.abi import get_selector_from_name

from starkware.cairo.common.hash_chain import compute_hash_chain
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile.common import get_contract_class, pt, QUERY_VERSION, TRANSACTION_VERSION, get_class_hash
from nile.core.types.utils import (
    get_execute_calldata,
    get_declare_hash,
    get_deploy_account_hash,
    get_invoke_hash,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_address

# Current supported version
TRANSACTION_VERSION = 1

# Version for query calls
QUERY_VERSION_BASE = 2**128
QUERY_VERSION = QUERY_VERSION_BASE + TRANSACTION_VERSION


@dataclasses.dataclass
class Transaction:
    """
    Starknet transaction abstraction.

    @param hash: The hash of the transaction.
    @param account_address: The account contract from which this transaction originates.
    @param contract_to_declare: Contract name for declarations.
    @param contract_class: Contract class required for declarations.
    @param class_hash: Class hash required for deployments.
    @param entry_point: The function to execute.
    @param entry_point_selector: The function selector.
    @param calldata: The parameters for the call.
    @param signature: The  signature of the transaction.
    @param max_fee: The maximal fee to be paid in Wei for the execution.
    @param nonce: The nonce of the transaction.
    @param network: The chain the transaction will be executed on.
    @param chain_id: The id of the chain the transaction will be executed on.
    @param version: The version of the transaction.
    @param overriding_path: Utility for artifacts resolution.
    """

    hash: int = field(init=False, default=0)
    account_address: int = 0
    contract_to_declare: str = None
    contract_class: str = field(init=False, default=None)
    class_hash: int = None
    tx_type: Literal["invoke", "declare", "deploy_account"] = "invoke"
    entry_point: str = "__execute__"
    entry_point_selector: int = field(init=False)
    calldata: List[int] = None
    signature: List[int] = field(init=False, default=None)
    max_fee: int = 0
    nonce: int = None
    network: str = "localhost"
    chain_id: int = field(init=False)
    version: int = TRANSACTION_VERSION
    overriding_path: str = None

    def __post_init__(self):
        """Initialize hash, entry_point_selector, contract_class and chain_id."""
        self.chain_id = (
            StarknetChainId.MAINNET.value
            if self.network == "mainnet"
            else StarknetChainId.TESTNET.value
        )

        if self.tx_type in ["invoke"]:
            self.hash = get_invoke_hash(
                self.account_address,
                self.calldata,
                self.max_fee,
                self.nonce,
                self.version,
                self.chain_id,
            )
        elif self.tx_type == "declare":
            self.contract_class = get_contract_class(
                contract_name=self.contract_to_declare,
                overriding_path=self.overriding_path,
            )

            self.hash = get_declare_hash(
                self.account_address,
                self.contract_class,
                self.max_fee,
                self.nonce,
                self.version,
                self.chain_id,
            )
        elif self.tx_type == "deploy_account":
            self.hash = get_deploy_account_hash(
                self.account_address,
                self.class_hash,
                self.calldata,
                self.max_fee,
                self.nonce,
                self.version,
                self.chain_id,
            )

        self.entry_point_selector = get_selector_from_name(self.entry_point)

        # Validate the transaction object
        self._validate()

    @classmethod
    def create_invoke(
        cls,
        account_address: int,
        calldata,
        max_fee: int,
        nonce: int,
        network: int,
        version: int,
    ) -> "Transaction":
        """Create an invoke transaction."""
        return cls(
            tx_type="invoke",
            account_address=account_address,
            calldata=calldata,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
        )

    @classmethod
    def create_declare(
        cls,
        account_address: int,
        contract_to_declare: str,
        max_fee: int,
        nonce: int,
        network: int,
        version: int,
    ) -> "Transaction":
        """Create a declare transaction."""
        return cls(
            tx_type="declare",
            account_address=account_address,
            contract_to_declare=contract_to_declare,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
        )

    @classmethod
    async def create_udc_deploy(
        cls,
        account,
        contract_name,
        salt,
        unique,
        calldata,
        deployer_address,
        max_fee,
        query_type=None,
        overriding_path=None,
        nonce=None,
    ):
        """Return a transaction representing a UDC deployment."""
        deployer_for_address_generation = 0

        if salt is None:
            salt = 0

        _salt = salt

        if unique:
            # Match UDC address generation
            _salt = compute_hash_chain(data=[account.address, salt])
            deployer_for_address_generation = deployer_address

        class_hash = get_class_hash(contract_name, overriding_path)

        predicted_address = calculate_contract_address_from_hash(
            _salt, class_hash, calldata, deployer_for_address_generation
        )

        max_fee, nonce, calldata = await account._process_arguments(
            max_fee, nonce, calldata
        )
        execute_calldata = get_execute_calldata(
            calls=[[deployer_address, "deployContract", calldata]]
        )
        tx_version = QUERY_VERSION if query_type else TRANSACTION_VERSION

        # Create transaction
        unsigned_transaction = cls.create_invoke(
            account_address=account.address,
            calldata=execute_calldata,
            max_fee=max_fee,
            nonce=nonce,
            network=account.network,
            version=tx_version,
        )

        return unsigned_transaction, predicted_address

    def sign(self, signer):
        """Update the transaction signature from a signer."""
        assert self.signature is None, "Attempt to sign a signed transaction"

        sig_r, sig_s = signer.sign(message_hash=self.hash)
        self.signature = [sig_r, sig_s]

        return self

    async def execute(self, **kwargs):
        """Execute the transaction."""
        assert self.signature is not None, "Attempt to execute an unsigned transaction"

        if self.tx_type == "invoke":
            type_specific_args = {
                "inputs": self.calldata,
                "address": hex_address(self.account_address),
                "abi": f"{pt}/artifacts/abis/Account.json",
                "method": self.entry_point,
            }
        elif self.tx_type == "declare":
            type_specific_args = {
                "contract_name": self.contract_to_declare,
                "sender": hex_address(self.account_address),
            }

        output = await execute_call(
            self.tx_type,
            self.network,
            signature=self.signature,
            max_fee=self.max_fee,
            query_flag=None,
            **type_specific_args,
            **kwargs,
        )

        match = re.search(r"Transaction hash: (0x[\da-f]{1,64})", output)
        output_tx_hash = match.groups()[0] if match else None

        assert output_tx_hash == hex(
            self.hash
        ), "Missmatching transaction hash in execution"

        return self.hash

    async def estimate_fee(self):
        """Estimate the fee of execution."""
        assert self.signature is not None, "Attempt to execute an unsigned transaction"

        await execute_call(
            self.tx_type,
            self.network,
            inputs=self.calldata,
            signature=self.signature,
            max_fee=self.max_fee,
            query_flag="estimate_fee",
            address=hex_address(self.account_address),
            abi=f"{pt}/artifacts/abis/Account.json",
            method=self.entry_point,
        )

    def _validate(self):
        """Validate the transaction object."""
        assert hash != 0, "Transaction hash is empty after transaction creation!"
