"""Functions used to find/track/debug a transaction status."""

import json
import logging
import os
import time
from collections import namedtuple
from enum import Enum

from nile.common import (
    BUILD_DIRECTORY,
    DEPLOYMENTS_FILENAME,
    RETRY_AFTER_SECONDS,
    get_addresses_from_string,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_class_hash

TransactionStatus = namedtuple(
    "TransactionStatus", ["tx_hash", "status", "error_message"]
)


async def status(
    tx_hash, network, watch_mode=None, contracts_file=None
) -> TransactionStatus:
    """Fetch a transaction status.

    Optionally track until resolved (accepted on L2 or rejected) and/or
    use available artifacts to help locate the error. Debug implies track.
    """
    logging.info(f"⏳ Transaction hash: {hex_class_hash(tx_hash)}")
    logging.info("⏳ Querying the network for transaction status...")

    while True:
        tx_status = await execute_call(
            "tx_status", network, hash=hex_class_hash(tx_hash)
        )
        raw_receipt = json.loads(tx_status)
        receipt = _get_tx_receipt(tx_hash, raw_receipt, watch_mode)
        if receipt is not None:
            break

    if not receipt.status.is_rejected:
        return TransactionStatus(tx_hash, receipt.status, None)

    error_message = receipt.receipt["tx_failure_reason"]["error_message"]
    if watch_mode == "debug":
        error_message = await debug_message(
            error_message, tx_hash, network, contracts_file
        )

    logging.info(f"🧾 Error message:\n{error_message}")

    return TransactionStatus(tx_hash, receipt.status, error_message)


_TransactionReceipt = namedtuple("TransactionReceipt", ["tx_hash", "status", "receipt"])


async def debug_message(error_message, tx_hash, network, contracts_file=None):
    """
    Use available contracts to help locate the error in a rejected transaction.

    @param error_message: Error message of the transaction receipt.
    @param tx_hash: Hash of the transaction.
    @param network: Network queried.
    @param contracts_file: File to use instead of the one generated automatically
      from network name.
    """
    addresses = get_addresses_from_string(error_message)

    if not addresses:
        logging.warning(
            "🛑 The transaction was rejected but no contract address was identified "
            "in the error message."
        )
        return error_message

    contracts = _get_contracts_data(contracts_file, network, addresses)

    if not contracts:
        logging.warning(
            "🛑 The transaction was rejected but no contract data is locally "
            "available to improve the error message."
        )
        return error_message

    logging.info(f"🧾 Found contracts: {contracts}")
    logging.info("⏳ Querying the network with identified contracts...")

    return await execute_call(
        "tx_status",
        network,
        hash=hex_class_hash(tx_hash),
        contracts=",".join(contracts),
        error_message=True,
    )


def _get_contracts_data(contracts_file, network, addresses):
    file = contracts_file or f"{network}.{DEPLOYMENTS_FILENAME}"
    to_contract = (lambda x: x) if contracts_file else _abi_to_path
    contracts = _locate_error_lines_with_abis(file, addresses, to_contract)
    return contracts


def _abi_to_path(filename):
    build_path = os.path.join(BUILD_DIRECTORY, os.path.basename(filename))
    if os.path.isfile(build_path):
        return build_path
    else:
        pt = os.path.dirname(os.path.realpath(__file__)).replace("/utils", "/artifacts")
        return os.path.join(pt, os.path.basename(filename))


def _locate_error_lines_with_abis(file, addresses, to_contract):
    contracts = []
    if not os.path.isfile(file):
        raise IOError(
            f"Contracts file {file} not found "
            "while trying to debug REJECTED transaction."
        )

    with open(file) as file_stream:
        for line_idx, line in enumerate(file_stream):
            try:
                line_address, abi, *_ = line.split(":")
            except ValueError:
                logging.warning(
                    f"⚠ Skipping misformatted line #{line_idx+1} in {file}."
                )
                continue
            if int(line.split(":")[0], 16) in addresses:
                contracts.append(f"{line_address}:{to_contract(abi.rstrip())}")

    return contracts


def _get_tx_receipt(tx_hash, raw_receipt, watch_mode) -> _TransactionReceipt:
    receipt = _TransactionReceipt(
        tx_hash, TxStatus.from_receipt(raw_receipt), raw_receipt
    )

    if receipt.status.is_rejected:
        logging.info(f"❌ Transaction status: {receipt.status}")
        return receipt

    log_output = f"Transaction status: {receipt.status}"

    if receipt.status.is_accepted:
        logging.info(f"✅ {log_output}. No error in transaction.")
        return receipt

    if watch_mode is None:
        logging.info(f"🕒 {log_output}.")
        return receipt

    logging.info(f"🕒 {log_output}. Trying again in {RETRY_AFTER_SECONDS} seconds...")
    time.sleep(RETRY_AFTER_SECONDS)


class TxStatus(Enum):
    """StarkNet Transactions Status."""

    REJECTED = 0
    NOT_RECEIVED = 1
    RECEIVED = 2
    PENDING = 3
    ACCEPTED_ON_L2 = 4
    ACCEPTED_ON_L1 = 5

    @property
    def is_accepted(self):
        """Whether transaction status is considered accepted."""
        return self in {TxStatus.ACCEPTED_ON_L1, TxStatus.ACCEPTED_ON_L2}

    @property
    def is_rejected(self):
        """Whether transaction status is considered rejected."""
        return self == TxStatus.REJECTED

    def __str__(self):
        """Restore StarkNet status label (with spaces)."""
        return self.name.replace("_", " ")

    @classmethod
    def from_receipt(cls, receipt):
        """Return the status corresponding to a StarkNet transaction receipt."""
        return cls[receipt["tx_status"].replace(" ", "_")]
