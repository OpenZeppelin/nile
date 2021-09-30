"""Command to compile cairo files."""
import os
import subprocess

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    CONTRACTS_DIRECTORY,
    get_all_contracts,
)


def compile_command(contracts):
    """Compile cairo contracts to default output directory."""
    # to do: automatically support subdirectories

    if not os.path.exists(ABIS_DIRECTORY):
        print(f"Creating {ABIS_DIRECTORY} to store compilation artifacts")
        os.makedirs(ABIS_DIRECTORY, exist_ok=True)

    if len(contracts) == 0:
        print(f"🤖 Compiling all Cairo contracts in the {CONTRACTS_DIRECTORY} directory")
        for path in get_all_contracts():
            _compile_contract(path)
    elif len(contracts) == 1:
        _compile_contract(contracts[0])
    else:
        for path in contracts:
            _compile_contract(path)

    print("✅ Done")


def _compile_contract(path):
    base = os.path.basename(path)
    filename = os.path.splitext(base)[0]
    print(f"🔨 Compiling {path}")

    cmd = f"""
    starknet-compile {path} \
        --cairo_path={CONTRACTS_DIRECTORY}
        --output {BUILD_DIRECTORY}{filename}.json \
        --abi {ABIS_DIRECTORY}{filename}.json
    """
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
