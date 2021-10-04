"""Command to kickstart a Nile project."""
import subprocess
import sys
from pathlib import Path

from nile.commands.install import install_command


def init_command():
    """Kickstart a new Nile project."""
    # install cairo dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "ecdsa", "fastecdsa", "sympy"]
    )

    # install cairo within env
    install_command()

    # install testing dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"]
    )
    print("")
    print("✅ Dependencies successfully installed")

    # create project directories
    print("🗄  Creating project directory tree")
    create_contracts()
    create_tests()

    with open("Makefile", "w") as fp:
        fp.write(makefile)

    print("⛵️ Nile project ready! Try running:")
    print("")
    print("nile compile")
    print("")


def create_contracts():
    """Create contracts/ directory."""
    Path("contracts/").mkdir(parents=True, exist_ok=True)
    with open("contracts/contract.cairo", "w") as fp:
        fp.write(contract)


def create_tests():
    """Create tests/ directory."""
    Path("tests/").mkdir(parents=True, exist_ok=True)
    with open("tests/test_contract.py", "w") as fp:
        fp.write(test)


contract = """# Declare this file as a StarkNet contract and set the required
# builtins.
%lang starknet
%builtins pedersen range_check

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.storage import Storage

# Define a storage variable.
@storage_var
func balance() -> (res : felt):
end

# Increases the balance by the given amount.
@external
func increase_balance{
        storage_ptr : Storage*, pedersen_ptr : HashBuiltin*,
        range_check_ptr}(amount : felt):
    let (res) = balance.read()
    balance.write(res + amount)
    return ()
end

# Returns the current balance.
@view
func get_balance{
        storage_ptr : Storage*, pedersen_ptr : HashBuiltin*,
        range_check_ptr}() -> (res : felt):
    let (res) = balance.read()
    return (res)
end
"""


test = """import os
import pytest

from starkware.starknet.testing.starknet import Starknet

# The path to the contract source code.
CONTRACT_FILE = os.path.join("contracts", "contract.cairo")


# The testing library uses python's asyncio. So the following
# decorator and the ``async`` keyword are needed.
@pytest.mark.asyncio
async def test_increase_balance():
    # Create a new Starknet class that simulates the StarkNet
    # system.
    starknet = await Starknet.empty()

    # Deploy the contract.
    contract = await starknet.deploy(CONTRACT_FILE)

    # Invoke increase_balance() twice.
    await contract.increase_balance(amount=10).invoke()
    await contract.increase_balance(amount=20).invoke()

    # Check the result of get_balance().
    assert await contract.get_balance().call() == (30,)
"""

makefile = """# Build and test
build :; nile compile
test  :; pytest tests/
"""
