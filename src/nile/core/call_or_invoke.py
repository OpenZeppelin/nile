"""Command to call or invoke StarkNet smart contracts."""
import logging
import re
import subprocess

from nile import deployments
from nile.common import GATEWAYS, prepare_params, get_network_parameter
from nile.core import account
from nile.utils import hex_address
from nile.utils.status import status


def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None, track=False, debug=False
):
    """Call or invoke functions of StarkNet smart contracts."""
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

    command += get_network_parameter(network, with_feeder=True)

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

    command.append("--no_wallet")

    try:
        output = subprocess.check_output(command).strip().decode("utf-8")
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

    if type != "call" and output:
        logging.info(output)
        transaction_hash = _get_transaction_hash(output)
        return status(transaction_hash, network, track, debug)

    return output


def _get_transaction_hash(string):
    match = re.search(r"Transaction hash: (0x[\da-f]{1,64})", string)
    return match.groups()[0] if match else None
