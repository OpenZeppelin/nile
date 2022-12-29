"""Starknet CLI overrides."""
import argparse
from types import SimpleNamespace
from typing import List, Optional

from starkware.starknet.cli.starknet_cli import (
    add_deploy_account_tx_arguments,
    assert_tx_received,
    compute_max_fee,
    get_gateway_client,
    need_simulate_tx,
    simulate_or_estimate_fee,
    validate_max_fee,
)
from starkware.starknet.services.api.gateway.transaction import DeployAccount

from nile.common import QUERY_VERSION, TRANSACTION_VERSION, get_account_class_hash
from nile.core.types.utils import get_counterfactual_address


async def deploy_account_no_wallet(args: argparse.Namespace, command_args: List[str]):
    """Override for straknet_cli deploy_account."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploys an initialized account contract to StarkNet. "
            "For more information, see new_account."
        )
    )
    add_deploy_account_tx_arguments(parser=parser)
    validate_max_fee(max_fee=args.max_fee)

    deploy_account_tx_for_simulate: Optional[DeployAccount] = None
    if need_simulate_tx(args=args, has_wallet=True):
        deploy_account_tx_for_simulate, _ = await create_deploy_account_tx(
            args=args,
            max_fee=args.max_fee if args.max_fee is not None else 0,
            query=True,
        )
        if args.simulate or args.estimate_fee:
            await simulate_or_estimate_fee(args=args, tx=deploy_account_tx_for_simulate)
            return

    assert args.block_hash is None and args.block_number is None, (
        "--block_hash and --block_number should only "
        "be passed when either --simulate or "
        "--estimate_fee flag are used."
    )
    max_fee = await compute_max_fee(
        args=args, tx=deploy_account_tx_for_simulate, has_wallet=True
    )

    tx, contract_address = await create_deploy_account_tx(
        args=args,
        max_fee=max_fee,
        query=False,
    )

    gateway_client = get_gateway_client(args)
    gateway_response = await gateway_client.add_transaction(tx=tx)
    assert_tx_received(gateway_response=gateway_response)
    # Verify the address received from the gateway.
    assert (
        actual_address := int(gateway_response["address"], 16)
    ) == contract_address, (
        f"The address returned from the Gateway: 0x{actual_address:064x} "
        f"does not match the address stored in the account: 0x{contract_address:064x}. "
        "Are you using the correct version of the CLI?"
    )

    print(
        f"""\
Sent deploy account contract transaction.

Contract address: 0x{contract_address:064x}
Transaction hash: {gateway_response['transaction_hash']}
"""
    )


async def create_deploy_account_tx(args, max_fee, query=False):
    """Create the DeployAccount Tx."""
    class_hash = get_account_class_hash(args.contract_name)
    predicted_address = get_counterfactual_address(args.salt, args.calldata)
    tx_version = QUERY_VERSION if query else TRANSACTION_VERSION

    tx = DeployAccount(
        class_hash=class_hash,
        constructor_calldata=args.calldata,
        contract_address_salt=args.salt,
        max_fee=max_fee,
        nonce=0,
        signature=args.signature,
        version=tx_version,
    )

    return tx, predicted_address


def update_deploy_account_context(args: SimpleNamespace, **kwargs):
    """Add deploy_account context to args."""
    extension = [
        "contract_name",
        "salt",
        "calldata",
        "signature",
        "max_fee",
        "simulate",
        "estimate_fee",
        "block_hash",
        "block_number",
    ]

    for arg in extension:
        setattr(args, arg, kwargs.get(arg))

    if kwargs.get("query_flag"):
        setattr(args, kwargs.get("query_flag"), True)

    return args
