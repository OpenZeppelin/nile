"""Transaction module."""

import dataclasses
import json
import logging
import re
from dataclasses import field
from typing import List, Literal

from starkware.cairo.common.hash_chain import compute_hash_chain
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)
from starkware.starknet.definitions.general_config import StarknetChainId
from starkware.starknet.public.abi import get_selector_from_name

from nile.common import TRANSACTION_VERSION, get_class_hash, get_contract_class, pt
from nile.core.types.utils import (
    get_declare_hash,
    get_deploy_account_hash,
    get_execute_calldata,
    get_invoke_hash,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_address
from nile.utils.status import status

# Version for query calls
QUERY_VERSION_BASE = 2**128


@dataclasses.dataclass
class Transaction:
    """
    Starknet transaction abstraction.

    Init params.

    @param account_address: The account contract from which this transaction originates.
    @param contract_to_submit: Contract name for declarations or deployments.
    @param class_hash: Class hash required for deployments.
    @param entry_point: The function to execute.
    @param calldata: The parameters for the call.
    @param max_fee: The maximal fee to be paid in Wei for the execution.
    @param nonce: The nonce of the transaction.
    @param network: The chain the transaction will be executed on.
    @param version: The version of the transaction.
    @param overriding_path: Utility for artifacts resolution.

    Generated internally.

    @param hash: The hash of the transaction.
    @param query_hash: The hash of the transaction with QUERY_VERSION.
    @param contract_class: Contract class required for declarations.
    @param chain_id: The id of the chain the transaction will be executed on.
    @param entry_point_selector: The function selector.
    """

    account_address: int = 0
    contract_to_submit: str = None
    class_hash: int = None
    tx_type: Literal["invoke", "declare", "deploy_account"] = "invoke"
    entry_point: str = "__execute__"
    calldata: List[int] = None
    max_fee: int = 0
    nonce: int = None
    network: str = "localhost"
    version: int = TRANSACTION_VERSION
    overriding_path: str = None

    # Public fields not expected in construction time
    hash: int = field(init=False, default=0)
    query_hash: int = field(init=False, default=0)
    chain_id: int = field(init=False)
    contract_class: str = field(init=False, default=None)
    entry_point_selector: int = field(init=False)

    # Internal fields
    _udc_deployment_address: int = field(init=False, default=None)

    def __post_init__(self):
        """Initialize hash, entry_point_selector, contract_class and chain_id."""
        self.chain_id = (
            StarknetChainId.MAINNET.value
            if self.network == "mainnet"
            else StarknetChainId.TESTNET.value
        )

        if self.tx_type == "invoke":
            get_tx_hash_func = self._get_invoke_hash
        elif self.tx_type == "declare":
            self.contract_class = get_contract_class(
                contract_name=self.contract_to_submit,
                overriding_path=self.overriding_path,
            )
            get_tx_hash_func = self._get_declare_hash
        elif self.tx_type == "deploy_account":
            get_tx_hash_func = self._get_deploy_account_hash

        self.hash = get_tx_hash_func()
        self.query_hash = get_tx_hash_func(QUERY_VERSION_BASE + self.version)
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
        version: int = TRANSACTION_VERSION,
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
        contract_to_submit: str,
        max_fee: int,
        nonce: int,
        network: int,
        version: int = TRANSACTION_VERSION,
    ) -> "Transaction":
        """Create a declare transaction."""
        return cls(
            tx_type="declare",
            account_address=account_address,
            contract_to_submit=contract_to_submit,
            max_fee=max_fee,
            nonce=nonce,
            network=network,
            version=version,
        )

    @classmethod
    async def create_udc_deploy(
        cls,
        account,
        contract_name: str,
        salt: int,
        unique: bool,
        calldata,
        deployer_address: int,
        max_fee: int,
        nonce: int = None,
        overriding_path=None,
    ) -> "Transaction":
        """Return a transaction representing a UDC deployment."""
        deployer_for_address_generation = 0

        if salt is None:
            salt = 0

        _salt = salt
        if unique:
            _salt = compute_hash_chain(data=[account.address, salt])
            deployer_for_address_generation = deployer_address

        max_fee, nonce, calldata = await account._process_arguments(
            max_fee, nonce, calldata
        )
        class_hash = get_class_hash(contract_name, overriding_path)

        execute_calldata = get_execute_calldata(
            calls=[
                [
                    deployer_address,
                    "deployContract",
                    [class_hash, salt, 1 if unique else 0, len(calldata), *calldata],
                ]
            ]
        )

        tx = cls.create_invoke(
            account_address=account.address,
            calldata=execute_calldata,
            max_fee=max_fee,
            nonce=nonce,
            network=account.network,
            version=TRANSACTION_VERSION,
        )
        tx.contract_to_submit = contract_name

        # Save udc deployment predicted address
        tx._udc_deployment_address = calculate_contract_address_from_hash(
            _salt, class_hash, calldata, deployer_for_address_generation
        )

        return tx

    async def execute(self, signer, watch_mode=None, **kwargs):
        """Execute the transaction."""
        sig_r, sig_s = signer.sign(message_hash=self.hash)

        type_specific_args = self._get_type_specific_args()

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

        type_specific_args = self._get_type_specific_args()

        output = await execute_call(
            self.tx_type,
            self.network,
            signature=[sig_r, sig_s],
            max_fee=self.max_fee,
            query_flag="estimate_fee",
            **type_specific_args,
            **kwargs,
        )

        match = re.search(r"The estimated fee is: (0x[\d]{1,64})", output)
        output_value = match.groups()[0] if match else None

        logging.info(output)
        return output_value

    async def simulate(self, signer, **kwargs):
        """Simulate the execution."""
        sig_r, sig_s = signer.sign(message_hash=self.query_hash)

        type_specific_args = self._get_type_specific_args()

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

    def udc_deployment_address(self):
        """Getter for the udc deployment address."""
        assert (
            self._udc_deployment_address is not None
        ), "Not udc deployment transaction"

        return self._udc_deployment_address

    def _validate(self):
        """Validate the transaction object."""
        assert hash != 0, "Transaction hash is empty after transaction creation!"

    def _get_invoke_hash(self, version=None):
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

    def _get_declare_hash(self, version=None):
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

    def _get_deploy_account_hash(self, version=None):
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

    def _get_type_specific_args(self):
        type_specific_args = {}
        if self.tx_type == "invoke":
            type_specific_args = {
                "inputs": self.calldata,
                "address": hex_address(self.account_address),
                "abi": f"{pt}/artifacts/abis/Account.json",
                "method": self.entry_point,
            }
        elif self.tx_type == "declare":
            type_specific_args = {
                "contract_name": self.contract_to_submit,
                "sender": hex_address(self.account_address),
            }
        return type_specific_args
