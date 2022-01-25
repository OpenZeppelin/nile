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


def compile(contracts):
    """Compile cairo contracts to default output directory."""
    # to do: automatically support subdirectories

    if not os.path.exists(ABIS_DIRECTORY):
        logging.info(f"📁 Creating {ABIS_DIRECTORY} to store compilation artifacts")
        os.makedirs(ABIS_DIRECTORY, exist_ok=True)

    all_contracts = contracts

    if len(contracts) == 0:
        logging.info(
            f"🤖 Compiling all Cairo contracts in the {CONTRACTS_DIRECTORY} directory"
        )
        all_contracts = get_all_contracts()

    results = [_compile_contract(contract) for contract in all_contracts]
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


def _compile_contract(path):
    base = os.path.basename(path)
    filename = os.path.splitext(base)[0]
    logging.info(f"🔨 Compiling {path}")

    cmd = f"""
    starknet-compile {path} \
        --cairo_path={CONTRACTS_DIRECTORY}
        --output {BUILD_DIRECTORY}/{filename}.json \
        --abi {ABIS_DIRECTORY}/{filename}.json
    """
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    process.communicate()
    return process.returncode
