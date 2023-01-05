"""Utilities for Nile scripting."""
# flake8: noqa

from .common import (
    add_uint,
    div_rem_uint,
    felt_to_str,
    from_uint,
    hex_address,
    hex_class_hash,
    mul_uint,
    normalize_number,
    shorten_address,
    str_to_felt,
    sub_uint,
    to_uint,
)

MAX_UINT256 = (2**128 - 1, 2**128 - 1)
INVALID_UINT256 = (MAX_UINT256[0] + 1, MAX_UINT256[1])
ZERO_ADDRESS = 0
TRUE = 1
FALSE = 0
