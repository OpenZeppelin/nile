"""Utilities for Nile scripting."""

import math
from pathlib import Path

try:
    from starkware.starknet.business_logic.execution.objects import Event
    from starkware.starknet.public.abi import get_selector_from_name
    from starkware.starkware_utils.error_handling import StarkException
except BaseException:
    pass

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
    felt = int(felt, 16) if "0x" in felt else int(felt)
    b_felt = felt.to_bytes(31, "big")
    return b_felt.decode()


def to_uint(a):
    """Return uint256-ish tuple from value."""
    a = int(a)
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
