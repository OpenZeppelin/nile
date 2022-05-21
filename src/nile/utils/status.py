"""Functions used to find/track/debug a transaction status."""

import json
import logging
import subprocess
import time
from collections import namedtuple
from enum import Enum

from nile.common import get_network_parameter, RETRY_AFTER_SECONDS
from nile.utils.debug import debug_message

TransactionStatus = namedtuple(
    "TransactionStatus", ["tx_hash", "status", "error_message"]
)


def status(
    tx_hash, network, track=False, debug=False, contracts_file=None
) -> TransactionStatus:
    """Fetch a transaction status.

    Optionally track until resolved (accepted on L2 or rejected) and/or
    use available contracts to help locate the error. Debug implies track.
    """
    command = ["starknet", "tx_status", "--hash", tx_hash]
    command += get_network_parameter(network)

    logging.info("⏳ Querying the network for transaction status...")

    receipt = _get_tx_receipt(tx_hash, command, track or debug)

    if not receipt.status.is_rejected:
        return TransactionStatus(tx_hash, receipt.status, None)

    error_message = receipt.receipt["tx_failure_reason"]["error_message"]
    if debug:
        error_message = debug_message(error_message, command, network, contracts_file)

    logging.info(f"🧾 Error message:\n{error_message}")

    return TransactionStatus(tx_hash, receipt.status, error_message)


_TransactionReceipt = namedtuple("TransactionReceipt", ["tx_hash", "status", "receipt"])


def _get_tx_receipt(tx_hash, command, track=False) -> _TransactionReceipt:
    while True:
        raw_receipt = json.loads(subprocess.check_output(command))
        receipt = _TransactionReceipt(
            tx_hash, Status.from_receipt(raw_receipt), raw_receipt
        )

        if receipt.status.is_rejected:
            logging.info(f"❌ Transaction status: {receipt.status}")
            return receipt

        log_output = f"Transaction status: {receipt.status}"

        if receipt.status.is_accepted:
            logging.info(f"✅ {log_output}. No error in transaction.")
            return receipt

        if not track:
            logging.info(f"🕒 {log_output}.")
            return receipt

        logging.info(f"🕒 {log_output}. Trying again in a moment...")
        time.sleep(RETRY_AFTER_SECONDS)


class Status(Enum):
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
        return self in {Status.ACCEPTED_ON_L1, Status.ACCEPTED_ON_L2}

    @property
    def is_rejected(self):
        """Whether transaction status is considered rejected."""
        return self == Status.REJECTED

    def __str__(self):
        """Restore StarkNet status label (with spaces)."""
        return self.name.replace("_", " ")

    @classmethod
    def from_receipt(cls, receipt):
        """Return the status corresponding to a StarkNet transaction receipt."""
        return cls[receipt["tx_status"].replace(" ", "_")]
