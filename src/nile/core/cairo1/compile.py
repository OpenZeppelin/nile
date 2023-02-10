"""Command to compile cairo1 files."""
import json
import logging
import os
import subprocess

from nile.common import CONTRACTS_DIRECTORY, get_all_contracts
from nile.core.cairo1.common import ABIS_DIRECTORY, BUILD_DIRECTORY, COMPILERS_BIN_PATH


def compile(
    contracts,
    directory=None,
):
    """Compile command."""
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

    results = []

    for contract in all_contracts:
        status_code, sierra_file, filename = _compile_to_sierra(
            contract, contracts_directory
        )
        results.append(status_code)
        if status_code == 0:
            _extract_abi(sierra_file, filename)
            _compile_to_casm(sierra_file, filename)

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


def _compile_to_sierra(
    path,
    directory=None,
):
    """Compile from Cairo1 to Sierra."""
    base = os.path.basename(path)
    filename = os.path.splitext(base)[0]
    logging.info(f"🔨 Compiling {path}")

    sierra_file = f"{BUILD_DIRECTORY}/{filename}.sierra"

    cmd = f"""
        {COMPILERS_BIN_PATH}/starknet-compile {path} \
        {sierra_file}
    """

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    process.communicate()

    return process.returncode, sierra_file, filename


def _compile_to_casm(sierra_file, filename):
    """Compile from Sierra to Casm."""
    cmd = f"""
        {COMPILERS_BIN_PATH}/starknet-sierra-compile {sierra_file} \
        {BUILD_DIRECTORY}/{filename}.casm
    """

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    process.communicate()
    return process.returncode


def _extract_abi(sierra_file, filename):
    with open(sierra_file, "r") as f:
        data = json.load(f)

    with open(f"{ABIS_DIRECTORY}/{filename}.json", "w") as f:
        json.dump(data["abi"], f, indent=2)
