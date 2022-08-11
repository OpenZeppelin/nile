"""Utilities for Cairo contracts."""

import math
import os
from pathlib import Path

from starkware.starknet.business_logic.execution.objects import Event
from starkware.starknet.compiler.compile import compile_starknet_files
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.testing.starknet import Starknet, StarknetContract
from starkware.starkware_utils.error_handling import StarkException

MAX_UINT256 = (2**128 - 1, 2**128 - 1)
INVALID_UINT256 = (MAX_UINT256[0] + 1, MAX_UINT256[1])
ZERO_ADDRESS = 0
TRUE = 1
FALSE = 0

TRANSACTION_VERSION = 0


_root = Path(__file__).parent.parent


def contract_path(name):
    """Return contract path."""
    if name.startswith("tests/"):
        return str(_root / name)
    else:
        return str(_root / "src" / name)


def str_to_felt(text):
    """Return a field element from a given string."""
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt):
    """Return a string from a given field element."""
    b_felt = felt.to_bytes(31, "big")
    return b_felt.decode()


def to_uint(a):
    """Return uint256-ish tuple from value."""
    return (a & ((1 << 128) - 1), a >> 128)


def from_uint(uint):
    """Return value from uint256-ish tuple."""
    return uint[0] + (uint[1] << 128)


def add_uint(a, b):
    """Return the sum of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a + b
    return to_uint(c)


def sub_uint(a, b):
    """Return the difference of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a - b
    return to_uint(c)


def mul_uint(a, b):
    """Return the product of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a * b
    return to_uint(c)


def div_rem_uint(a, b):
    """Return the quotient and remainder of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = math.trunc(a / b)
    m = a % b
    return (to_uint(c), to_uint(m))


async def assert_revert(fun, reverted_with=None):
    """Raise if passed function does not revert."""
    try:
        await fun
        raise AssertionError("Transaction did not revert")
    except StarkException as err:
        _, error = err.args
        if reverted_with is not None:
            assert reverted_with in error["message"]


async def assert_revert_entry_point(fun, invalid_selector):
    """Raise is passed function does not revert with invalid selector."""
    selector_hex = hex(get_selector_from_name(invalid_selector))
    entry_point_msg = f"Entry point {selector_hex} not found in contract"

    await assert_revert(fun, entry_point_msg)


def assert_event_emitted(tx_exec_info, from_address, name, data):
    """Raise if event and event items do not match."""
    assert (
        Event(
            from_address=from_address,
            keys=[get_selector_from_name(name)],
            data=data,
        )
        in tx_exec_info.raw_events
    )


def _get_path_from_name(name):
    """Return the contract path by contract name."""
    dirs = ["src", "tests/mocks"]
    for dir in dirs:
        for (dirpath, _, filenames) in os.walk(dir):
            for file in filenames:
                if file == f"{name}.cairo":
                    return os.path.join(dirpath, file)

    raise FileNotFoundError(f"Cannot find '{name}'.")


def get_contract_class(contract, is_path=False):
    """Return the contract class from the contract name or path."""
    if is_path:
        path = contract_path(contract)
    else:
        path = _get_path_from_name(contract)

    contract_class = compile_starknet_files(files=[path], debug_info=True)
    return contract_class


def cached_contract(state, _class, deployed):
    """Return the cached contract."""
    contract = StarknetContract(
        state=state,
        abi=_class.abi,
        contract_address=deployed.contract_address,
        deploy_execution_info=deployed.deploy_execution_info,
    )
    return contract


class State:
    """
    Utility helper for Account class to initialize and return StarkNet state.

    Example
    ---------
    Initalize StarkNet state

    >>> starknet = await State.init()

    """

    async def init():
        """Initialize the StarkNet state."""
        global starknet
        starknet = await Starknet.empty()
        return starknet


class Account:
    """
    Utility for deploying Account contract.

    Parameters
    ----------
    public_key : int

    Examples
    ----------
    >>> starknet = await State.init()
    >>> account = await Account.deploy(public_key)

    """

    get_class = get_contract_class("Account")

    @staticmethod
    async def deploy(public_key):
        """Deploy account with public key."""
        account = await starknet.deploy(
            contract_class=Account.get_class, constructor_calldata=[public_key]
        )
        return account
