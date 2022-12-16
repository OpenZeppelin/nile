"""Transaction module."""

import dataclasses
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import field
from typing import List

from nile.common import TRANSACTION_VERSION, get_chain_id, get_contract_class, pt
from nile.utils.status import status
from nile.core.types.utils import (
    get_declare_hash,
    get_deploy_account_hash,
    get_invoke_hash,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_address

# Version for query calls
QUERY_VERSION_BASE = 2**128


@dataclasses.dataclass
class Transaction(ABC):
    """
    Starknet transaction abstraction.

    Init params.

    @param account_address: The account contract from which this transaction originates.
    @param max_fee: The maximal fee to be paid in Wei for the execution.
    @param nonce: The nonce of the transaction.
    @param network: The chain the transaction will be executed on.
    @param version: The version of the transaction.

    Generated internally.

    @param hash: The hash of the transaction.
    @param query_hash: The hash of the transaction with QUERY_VERSION.
    @param chain_id: The id of the chain the transaction will be executed on.
    """

    account_address: int = 0
    max_fee: int = 0
    nonce: int = None
    network: str = "localhost"
    version: int = TRANSACTION_VERSION

    # Public fields not expected in construction time
    tx_type: int = field(init=False)
    hash: int = field(init=False, default=0)
    query_hash: int = field(init=False, default=0)
    chain_id: int = field(init=False)

    def __post_init__(self):
        """Populate pending fields."""
        self.chain_id = get_chain_id(self.network)
        self.hash = self._get_tx_hash()
        self.query_hash = self._get_tx_hash(QUERY_VERSION_BASE + self.version)

        # Validate the transaction object
        self._validate()

    async def execute(self, signer, watch_mode=None, **kwargs):
        """Execute the transaction."""
        sig_r, sig_s = signer.sign(message_hash=self.hash)

        type_specific_args = self._execute_call_args()

        output = await execute_call(
            self.tx_type,
            self.network,
            signature=[sig_r, sig_s],
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

        tx_status = await status(self.hash, self.network, watch_mode)
        return tx_status, output

    async def estimate_fee(self, signer, **kwargs):
        """Estimate the fee of execution."""
        sig_r, sig_s = signer.sign(message_hash=self.query_hash)

        type_specific_args = self._execute_call_args()

        output = await execute_call(
            self.tx_type,
            self.network,
            signature=[sig_r, sig_s],
            max_fee=self.max_fee,
            query_flag="estimate_fee",
            **type_specific_args,
            **kwargs,
        )

        match = re.search(r"The estimated fee is: [\d]{1,64}", output)
        output_value = (
            int(match.group(0).replace("The estimated fee is: ", "")) if match else None
        )

        logging.info(output)
        return output_value

    async def simulate(self, signer, **kwargs):
        """Simulate the execution."""
        sig_r, sig_s = signer.sign(message_hash=self.query_hash)

        type_specific_args = self._execute_call_args()

        output = await execute_call(
            self.tx_type,
            self.network,
            signature=[sig_r, sig_s],
            max_fee=self.max_fee,
            query_flag="simulate",
            **type_specific_args,
            **kwargs,
        )

        json_str = output.split("\n", 4)[4]
        output_value = json.loads(json_str)

        logging.info(output)
        return output_value

    @abstractmethod
    def _execute_call_args(self):
        """
        Return specific arguments from transaction type.

        This method must be overrided on each specific implementation.
        """
        return {}

    def _validate(self):
        """Validate the transaction object."""
        assert hash != 0, "Transaction hash is empty after transaction creation!"


@dataclasses.dataclass
class InvokeTransaction(Transaction):
    """
    Starknet invoke transaction abstraction.

    @param entry_point: The function to execute.
    @param calldata: The parameters for the call.
    """

    entry_point: str = "__execute__"
    calldata: List[int] = None

    def __post_init__(self):
        """Populate pending fields."""
        super().__post_init__()
        self.tx_type = "invoke"

    def _get_tx_hash(self, version=None):
        if not version:
            version = self.version

        return get_invoke_hash(
            self.account_address,
            self.calldata,
            self.max_fee,
            self.nonce,
            version,
            self.chain_id,
        )

    def _execute_call_args(self):
        return {
            "inputs": self.calldata,
            "address": hex_address(self.account_address),
            "abi": f"{pt}/artifacts/abis/Account.json",
            "method": self.entry_point,
        }


@dataclasses.dataclass
class DeclareTransaction(Transaction):
    """
    Starknet declare transaction abstraction.

    @param contract_to_submit: Contract name for declarations or deployments.
    @param contract_class: Contract class required for declarations.
    @param overriding_path: Utility for artifacts resolution.
    """

    contract_to_submit: str = None
    contract_class: str = field(init=False, default=None)
    overriding_path: str = None

    def __post_init__(self):
        """Populate pending fields."""
        self.contract_class = get_contract_class(
            contract_name=self.contract_to_submit,
            overriding_path=self.overriding_path,
        )
        self.tx_type = "declare"
        super().__post_init__()

    def _get_tx_hash(self, version=None):
        if not version:
            version = self.version

        return get_declare_hash(
            self.account_address,
            self.contract_class,
            self.max_fee,
            self.nonce,
            version,
            self.chain_id,
        )

    def _execute_call_args(self):
        return {
            "contract_name": self.contract_to_submit,
            "sender": hex_address(self.account_address),
        }


@dataclasses.dataclass
class DeployAccountTransaction(Transaction):
    """
    Starknet deploy_account transaction abstraction.

    @param contract_to_submit: Contract name for declarations or deployments.
    @param calldata: The parameters for the call.
    @param overriding_path: Utility for artifacts resolution.
    @param contract_class: Contract class required for declarations.
    """

    contract_to_submit: str = None
    calldata: List[int] = None
    overriding_path: str = None
    contract_class: str = field(init=False, default=None)

    def __post_init__(self):
        """Populate pending fields."""
        self.contract_class = get_contract_class(
            contract_name=self.contract_to_submit,
            overriding_path=self.overriding_path,
        )
        self.tx_type = "deploy_account"
        super().__post_init__()

    def _get_tx_hash(self, version=None):
        if not version:
            version = self.version

        return get_deploy_account_hash(
            self.account_address,
            self.class_hash,
            self.calldata,
            self.max_fee,
            self.nonce,
            version,
            self.chain_id,
        )

    def _execute_call_args(self):
        return {}
