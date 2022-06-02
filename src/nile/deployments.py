"""nile common module."""
import logging
import os

from nile.common import DEPLOYMENTS_FILENAME


def register(address, abi, network, alias):
    """Register a new deployment."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if alias is not None:
        if exists(alias, network):
            raise Exception(f"Alias {alias} already exists in {file}")

    with open(file, "a") as fp:
        if alias is not None:
            logging.info(f"📦 Registering deployment as {alias} in {file}")
        else:
            logging.info(f"📦 Registering {address} in {file}")

        fp.write(f"{address}:{abi}")
        if alias is not None:
            fp.write(f":{alias}")
        fp.write("\n")


def exists(identifier, network):
    """Return whether a deployment exists or not."""
    foo = next(load(identifier, network), None)
    return foo is not None


def load(identifier, network):
    """Load deployments that matches an identifier (address or alias)."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        logging.warning(
            f"⚠ No deployment file for the {network!r} network."
            " Did you specify the proper network using `--network NETWORK`?"
        )
        return

    with open(file) as fp:
        identifier_found = False
        for line in fp:
            [address, abi, *alias] = line.strip().split(":")
            if identifier in [address] + alias:
                identifier_found = True
                yield address, abi

        if not identifier_found:
            logging.warning(
                f"⚠ Contract {identifier!r} not found on the {network!r} network."
                " Did you deploy it first?"
                " Did you specify the proper network using `--network NETWORK`?"
            )
