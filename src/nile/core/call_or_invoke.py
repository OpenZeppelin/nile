"""Command to call or invoke StarkNet smart contracts."""
import logging
import re
import subprocess

from nile import deployments
from nile.common import get_network_parameter
from nile.utils.status import status


def call_or_invoke(
    contract,
    type,
    method,
    params,
    network,
    signature=None,
    max_fee=None,
    track=False,
    debug=False,
):
    """Call or invoke functions of StarkNet smart contracts."""
    address, abi = next(deployments.load(contract, network))

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
    command += get_network_parameter(
        network, "feeder_gateway" if type == "call" else "gateway"
    )

    if len(params) > 0:
        command.append("--inputs")
        command.extend(params)

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    if max_fee is not None:
        command.append("--max_fee")
        command.append(max_fee)

    try:
        output = subprocess.check_output(command).strip().decode("utf-8")

    except subprocess.CalledProcessError:
        p = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, error = p.communicate()

        if "max_fee must be bigger than 0" in error.decode():
            logging.error(
                """
                \n😰 Whoops, looks like max fee is missing. Try with:\n
                --max_fee=`MAX_FEE`
                """
            )
            output = None
        else:
            raise

    if type != "call" and output:
        logging.info(output)
        transaction_hash = _get_transaction_hash(output)
        return status(transaction_hash, network, track, debug)

    return output


def _get_transaction_hash(string):
    match = re.search(r"Transaction hash: (0x[\da-f]{1,64})", string)
    return match.groups()[0] if match else None
