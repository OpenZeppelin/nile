"""Functions used to help debug a rejected transaction."""

import logging
import os

from nile.common import BUILD_DIRECTORY, DEPLOYMENTS_FILENAME, get_addresses_from_string
from nile.starknet_cli import execute_call
from nile.utils import hex_class_hash


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

    execute_args = {
        "cmd_name": "tx_status",
        "network": network,
        "hash": hex_class_hash(tx_hash),
        "contracts": ",".join(contracts),
        "error_message": True,
    }

    try:
        return await execute_call(**execute_args)
    except FileNotFoundError:
        # Change path in contracts to locate Nile artifacts
        contracts = _get_contracts_data(contracts_file, network, addresses, True)
        execute_args["contracts"] = ",".join(contracts)
        return await execute_call(**execute_args)


def _get_contracts_data(contracts_file, network, addresses, nile_artifacts=False):
    file = contracts_file or f"{network}.{DEPLOYMENTS_FILENAME}"
    # contracts_file should already link to compiled contracts and not ABIs
    to_contract = (
        (lambda x: x)
        if contracts_file
        else _abi_to_nile_artifacts_path
        if nile_artifacts
        else _abi_to_build_path
    )
    contracts = _locate_error_lines_with_abis(file, addresses, to_contract)
    return contracts


def _abi_to_nile_artifacts_path(filename):
    pt = os.path.dirname(os.path.realpath(__file__)).replace("/utils", "/artifacts")
    return os.path.join(pt, os.path.basename(filename))


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
