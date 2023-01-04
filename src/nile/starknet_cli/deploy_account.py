"""Starknet CLI deploy_account override."""

import argparse
from types import SimpleNamespace
from typing import List

from starkware.starknet.cli.starknet_cli import (
    assert_tx_received,
    get_gateway_client,
    simulate_or_estimate_fee,
)
from starkware.starknet.services.api.gateway.transaction import DeployAccount

from nile.common import QUERY_VERSION, TRANSACTION_VERSION, get_account_class_hash
from nile.core.types.utils import get_counterfactual_address


async def deploy_account_no_wallet(args: argparse.Namespace, command_args: List[str]):
    """Override for starknet_cli deploy_account logic."""
    if args.simulate or args.estimate_fee:
        deploy_account_tx_for_simulate, _ = await create_deploy_account_tx(
            args=args,
            query=True,
        )
        await simulate_or_estimate_fee(args=args, tx=deploy_account_tx_for_simulate)
        return

    tx, contract_address = await create_deploy_account_tx(
        args=args,
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


async def create_deploy_account_tx(args, query=False):
    """Create the DeployAccount Tx."""
    class_hash = get_account_class_hash(args.contract_name)
    predicted_address = get_counterfactual_address(args.salt, args.calldata)
    tx_version = QUERY_VERSION if query else TRANSACTION_VERSION

    tx = DeployAccount(
        class_hash=class_hash,
        constructor_calldata=args.calldata,
        contract_address_salt=args.salt,
        max_fee=args.max_fee or 0,
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
