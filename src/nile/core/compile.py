"""Command to compile cairo files."""
import logging
import os
import subprocess

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    CONTRACTS_DIRECTORY,
    get_all_contracts,
)


def compile(
    contracts, directory=None, account_contract=False, disable_hint_validation=False
):
    """Compile cairo contracts to default output directory."""
    # to do: automatically support subdirectories

    contracts_directory = directory if directory else CONTRACTS_DIRECTORY

    if not os.path.exists(ABIS_DIRECTORY):
        logging.info(f"📁 Creating {ABIS_DIRECTORY} to store compilation artifacts")
        os.makedirs(ABIS_DIRECTORY, exist_ok=True)

    all_contracts = contracts

    if len(contracts) == 0:
        logging.info(
            f"🤖 Compiling all Cairo contracts in the {contracts_directory} directory"
        )
        all_contracts = get_all_contracts(directory=contracts_directory)

    results = [
        _compile_contract(
            contract, contracts_directory, account_contract, disable_hint_validation
        )
        for contract in all_contracts
    ]
    failed_contracts = [c for (c, r) in zip(all_contracts, results) if r != 0]
    failures = len(failed_contracts)

    if failures == 0:
        logging.info("✅ Done")
    else:
        exp = f"{failures} contract"
        if failures > 1:
            exp += "s"  # pluralize
        logging.info(f"🛑 Failed to compile the following {exp}:")
        for contract in failed_contracts:
            logging.info(f"   {contract}")


def _compile_contract(
    path, directory=None, account_contract=False, disable_hint_validation=False
):
    base = os.path.basename(path)
    filename = os.path.splitext(base)[0]
    logging.info(f"🔨 Compiling {path}")
    contracts_directory = directory if directory else CONTRACTS_DIRECTORY

    cmd = f"""
    starknet-compile {path} \
        --cairo_path={contracts_directory}
        --output {BUILD_DIRECTORY}/{filename}.json \
        --abi {ABIS_DIRECTORY}/{filename}.json
    """

    if account_contract:
        cmd = cmd + "--account_contract"

    if disable_hint_validation:
        cmd = cmd + "--disable_hint_validation"

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    process.communicate()
    return process.returncode
