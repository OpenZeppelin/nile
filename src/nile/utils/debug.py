"""Functions used to help debug a rejected transaction."""

import json
import logging
import os
import re
import subprocess
import time

from nile.common import (
    BUILD_DIRECTORY,
    DEPLOYMENTS_FILENAME,
    GATEWAYS,
    RETRY_AFTER_SECONDS,
)


def debug(tx_hash, network, contracts_file=None):
    """Use available contracts to help locate the error in a rejected transaction."""
    command = ["starknet", "tx_status", "--hash", tx_hash]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")

    logging.info(
        "⏳ Querying the network to check transaction status and identify contracts..."
    )

    while True:
        receipt = json.loads(subprocess.check_output(command))
        status = receipt["tx_status"]
        if status == "REJECTED":
            break
        output = f"Transaction status: {status}"
        if status.startswith("ACCEPTED"):
            logging.info(f"✅ {output}. No error in transaction.")
            return

        logging.info(f"🕒 {output}. Trying again in a moment...")
        time.sleep(RETRY_AFTER_SECONDS)

    error_message = receipt["tx_failure_reason"]["error_message"]
    addresses = set(
        int(address, 16)
        for address in re.findall("0x[\\da-f]{1,64}", str(error_message))
    )

    if not addresses:
        logging.warning(
            "🛑 The transaction was rejected but no contract address was identified "
            "in the error message."
        )
        logging.info(f"Error message:\n{error_message}")
        return error_message

    file = contracts_file or f"{network}.{DEPLOYMENTS_FILENAME}"
    # contracts_file should already link to compiled contracts and not ABIs
    to_contract = (lambda x: x) if contracts_file else _abi_to_build_path

    contracts = _locate_error_lines_with_abis(file, addresses, to_contract)

    if not contracts:
        logging.warning(
            "🛑 The transaction was rejected but no contract data is locally "
            "available to improve the error message."
        )
        logging.info(error_message)
        return error_message

    command += ["--contracts", ",".join(contracts), "--error_message"]
    logging.info(f"🧾 Found contracts: {contracts}")
    logging.info("⏳ Querying the network with identified contracts...")
    output = subprocess.check_output(command)

    logging.info(f"🧾 Error message:\n{output.decode()}")
    return output


def _abi_to_build_path(filename):
    return os.path.join(BUILD_DIRECTORY, os.path.basename(filename))


def _locate_error_lines_with_abis(file, addresses, to_contract):
    contracts = []
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
