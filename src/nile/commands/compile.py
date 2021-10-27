"""Command to compile cairo files."""
import os
import subprocess
import click
import functools
from typing import TypedDict

from nile.common import (ABIS_DIRECTORY, BUILD_DIRECTORY, CONTRACTS_DIRECTORY,
                         get_all_contracts)


class CompilationOptions(TypedDict):
    disable_hint_validation: bool


def compilation_params(func):
    @click.option('--disable_hint_validation')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def compile_command(contracts, compilation_opt: CompilationOptions):
    """Compile cairo contracts to default output directory."""
    # to do: automatically support subdirectories

    if not os.path.exists(ABIS_DIRECTORY):
        print(f"📁 Creating {ABIS_DIRECTORY} to store compilation artifacts")
        os.makedirs(ABIS_DIRECTORY, exist_ok=True)

    if len(contracts) == 0:
        print(f"🤖 Compiling all Cairo contracts in the {CONTRACTS_DIRECTORY} directory")
        for path in get_all_contracts():
            _compile_contract(path, compilation_opt)
    elif len(contracts) == 1:
        _compile_contract(contracts[0], compilation_opt)
    else:
        for path in contracts:
            _compile_contract(path, compilation_opt)

    print("✅ Done")


def _compile_contract(path, compilation_opt: CompilationOptions):
    base = os.path.basename(path)
    filename = os.path.splitext(base)[0]
    print(f"🔨 Compiling {path}")

    cmd = f"""
    starknet-compile {path} \
        --cairo_path={CONTRACTS_DIRECTORY}
        --output {BUILD_DIRECTORY}{filename}.json \
        --abi {ABIS_DIRECTORY}{filename}.json
    """

    # Parse options
    if(compilation_opt["disable_hint_validation"]):
        cmd += "--disable_hint_validation\n"
    
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

