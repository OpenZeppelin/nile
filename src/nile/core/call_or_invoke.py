"""Command to call or invoke StarkNet smart contracts."""
import logging
import os
import subprocess

from nile import deployments
from nile.common import GATEWAYS, prepare_params
from nile.core import account
from nile.utils import hex_address


def call_or_invoke(
    contract,
    type,
    method,
    params,
    network,
    signature=None,
    max_fee=None,
    query_flag=None,
):
    """
    Call or invoke functions of StarkNet smart contracts.

    @param contract: can be an address, and alias, or an Account instance.
    @param type: can be either call or invoke.
    @param method: the targeted function.
    @param params: the targeted function arguments.
    @param network: goerli, mainnet, or predefined networks file.
    @param signature: optional signature for invoke transactions.
    @param max_fee: optional max fee for invoke transactions.
    @param query_flag: either simulate or estimate_fee
    """
    if isinstance(contract, account.Account):
        address = contract.address
        abi = contract.abi_path
    else:
        address, abi = next(deployments.load(contract, network))

    address = hex_address(address)
    command = [
        "starknet",
        type,
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    params = prepare_params(params)

    if len(params) > 0:
        command.append("--inputs")
        command.extend(params)

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    if max_fee is not None:
        command.append("--max_fee")
        command.append(max_fee)

    if query_flag is not None:
        command.append(f"--{query_flag}")

    command.append("--no_wallet")

    try:
        return subprocess.check_output(command).strip().decode("utf-8")
    except subprocess.CalledProcessError:
        p = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, error = p.communicate()
        err_msg = error.decode()

        if "max_fee must be bigger than 0" in err_msg:
            logging.error(
                """
                \n😰 Whoops, looks like max fee is missing. Try with:\n
                --max_fee=`MAX_FEE`
                """
            )
        elif "transactions should go through the __execute__ entrypoint." in err_msg:
            logging.error(
                "\n\n😰 Whoops, looks like you're not using an account. Try with:\n"
                "\nnile send [OPTIONS] SIGNER CONTRACT_NAME METHOD [PARAMS]"
            )

        return ""
