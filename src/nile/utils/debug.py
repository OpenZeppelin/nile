"""Functions used to help debug a rejected transaction."""

import logging
import os
import re
import subprocess

from nile.common import BUILD_DIRECTORY, DEPLOYMENTS_FILENAME


def debug_message(error_message, command, network, contracts_file=None):
    """
    Use available contracts to help locate the error in a rejected transaction.

    :param error_message: error message of the transaction receipt.
    :param command: StarkNet CLI command used to get the transaction receipt.
    :param network: Network queried
    :param contracts_file: File to use instead of the one generated automatically
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

    command += ["--contracts", ",".join(contracts), "--error_message"]
    logging.info(f"🧾 Found contracts: {contracts}")
    logging.info("⏳ Querying the network with identified contracts...")
    output = subprocess.check_output(command)
    return output.decode()


def get_addresses_from_string(string):
    """Return a set of integers with identified addresses in a string."""
    return set(
        int(address, 16) for address in re.findall("0x[\\da-f]{1,64}", str(string))
    )


def _get_contracts_data(contracts_file, network, addresses):
    file = contracts_file or f"{network}.{DEPLOYMENTS_FILENAME}"
    # contracts_file should already link to compiled contracts and not ABIs
    to_contract = (lambda x: x) if contracts_file else _abi_to_build_path
    contracts = _locate_error_lines_with_abis(file, addresses, to_contract)
    return contracts


def _abi_to_build_path(filename):
    return os.path.join(BUILD_DIRECTORY, os.path.basename(filename))


def _locate_error_lines_with_abis(file, addresses, to_contract):
    contracts = []
    if not os.path.isfile(file):
        raise IOError(f"Contracts file {file} not found.")

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
