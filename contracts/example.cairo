%lang starknet
%builtins pedersen range_check ecdsa bitwise

from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.cairo_builtins import BitwiseBuiltin
from starkware.starknet.common.storage import Storage

@external
func sum{
        storage_ptr: Storage*,
        pedersen_ptr: HashBuiltin*,
        range_check_ptr
    } (a: felt, b: felt) -> (res: felt):
    alloc_locals
    local res
    %{ 
        ids.res = ids.a % ids.b
    %}
    return (res)
end