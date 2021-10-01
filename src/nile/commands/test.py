"""Command to run Cairo tests written in Cairo."""
import asyncio

from nile.common import CONTRACTS_DIRECTORY, get_all_contracts


def test_command(contracts):
    """Compile and run all provided Cairo tests."""
    asyncio.run(_test_command(contracts))


async def _test_command(contracts):
    if len(contracts) == 0:
        print(
            f"🤖 Running all test Cairo contracts in the {CONTRACTS_DIRECTORY} directory"
        )
        for path in get_all_contracts(".test.cairo"):
            await _run_test_contract(path)
    else:
        for path in contracts:
            await _run_test_contract(path)


async def _run_test_contract(path):
    # we dinamically import starknet dependencies because
    # this module is loaded on the first nile execution,
    # potentially before installing Cairo
    from starkware.starknet.compiler.compile import compile_starknet_files
    from starkware.starknet.testing.state import StarknetState
    from starkware.starkware_utils.error_handling import StarkException

    print(f"Running tests for {path}")
    definition = compile_starknet_files([path], debug_info=True)
    starknet = await StarknetState.empty()
    contract_addr = await starknet.deploy(definition)

    for abi_entry in definition.abi:
        if abi_entry["type"] != "function":
            continue
        func_name = abi_entry["name"]
        if not func_name.startswith("test"):
            continue
        local_starknet = starknet.copy()
        try:
            await local_starknet.invoke_raw(
                contract_address=contract_addr,
                selector=func_name,
                calldata=[0 for _ in abi_entry["inputs"]],
            )
            print(f"[PASS] {func_name}")
        except StarkException as ex:
            print(f"[FAIL] {func_name}")
            print(ex.message)
