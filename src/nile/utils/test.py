"""Utilities for testing."""

from starkware.starknet.business_logic.execution.objects import Event
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starkware_utils.error_handling import StarkException


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
    """Raise if passed function does not revert with invalid selector."""
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
