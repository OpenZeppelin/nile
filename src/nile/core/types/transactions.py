"""Transaction module."""

import dataclasses
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import field
from typing import List

from nile.common import (
    NILE_ABIS_DIR,
    QUERY_VERSION_BASE,
    TRANSACTION_VERSION,
    get_chain_id,
    get_class_hash,
    get_contract_class,
)
from nile.core.types.utils import (
    get_declare_hash,
    get_deploy_account_hash,
    get_invoke_hash,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_address
from nile.utils.status import status


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
    nonce: int = 0
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

        type_specific_args = self._get_execute_call_args()

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
        ), "Resulting transaction hash is different than expected"

        tx_status = await status(self.hash, self.network, watch_mode)
        return tx_status, output

    async def estimate_fee(self, signer, **kwargs):
        """Estimate the fee of execution."""
        sig_r, sig_s = signer.sign(message_hash=self.query_hash)

        type_specific_args = self._get_execute_call_args()

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

        type_specific_args = self._get_execute_call_args()

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

    def update_fee(self, max_fee):
        """Update the tx from a new max_fee."""
        self.max_fee = max_fee
        self.hash = self._get_tx_hash()
        self.query_hash = self._get_tx_hash(QUERY_VERSION_BASE + self.version)

        # Allow chaining with execute
        return self

    @abstractmethod
    def _get_execute_call_args(self):
        """
        Return specific arguments from transaction type.

        This method must be overridden on each specific implementation.
        """

    @abstractmethod
    def _get_tx_hash(self, version):
        """
        Return the tx hash for the transaction type.

        This method must be overridden on each specific implementation.
        """

    def _validate(self):
        """Validate the transaction object."""
        assert self.hash > 0, "Transaction hash is empty after transaction creation!"


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
        return get_invoke_hash(
            self.account_address,
            self.calldata,
            self.max_fee,
            self.nonce,
            version or self.version,
            self.chain_id,
        )

    def _get_execute_call_args(self):
        return {
            "inputs": self.calldata,
            "address": hex_address(self.account_address),
            "abi": f"{NILE_ABIS_DIR}/Account.json",
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
    contract_class: str = field(init=False)
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
        return get_declare_hash(
            self.account_address,
            self.contract_class,
            self.max_fee,
            self.nonce,
            version or self.version,
            self.chain_id,
        )

    def _get_execute_call_args(self):
        return {
            "contract_name": self.contract_to_submit,
            "overriding_path": self.overriding_path,
            "sender": hex_address(self.account_address),
        }


@dataclasses.dataclass
class DeployAccountTransaction(Transaction):
    """
    Starknet deploy_account transaction abstraction.

    @param salt: Deployed account address salt.
    @param contract_to_submit: Contract name for declarations or deployments.
    @param predicted_address: Counterfactual address of the account to deploy.
    @param calldata: The parameters for the call.
    @param overriding_path: Utility for artifacts resolution.
    @param contract_class: Contract class required for declarations.
    """

    salt: int = 0
    contract_to_submit: str = None
    predicted_address: int = 0
    calldata: List[int] = None
    overriding_path: str = None
    class_hash: int = field(init=False)

    def __post_init__(self):
        """Populate pending fields."""
        self.class_hash = get_class_hash(
            contract_name=self.contract_to_submit,
            overriding_path=self.overriding_path,
        )
        self.tx_type = "deploy_account"
        super().__post_init__()

    def _get_tx_hash(self, version=None):
        return get_deploy_account_hash(
            self.predicted_address,
            self.class_hash,
            self.calldata,
            self.salt,
            self.max_fee,
            self.nonce,
            version or self.version,
            self.chain_id,
        )

    def _get_execute_call_args(self):
        return {
            "salt": self.salt,
            "contract_name": self.contract_to_submit,
            "overriding_path": self.overriding_path,
            "calldata": self.calldata,
        }
