"""nile common module."""
import logging
import os

from nile.common import DECLARATIONS_FILENAME, DEPLOYMENTS_FILENAME
from nile.utils import hex_address, normalize_number


def register(address, abi, network, alias):
    """Register a new deployment."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if alias is not None:
        if exists(alias, network):
            raise Exception(f"Alias {alias} already exists in {file}")

    with open(file, "a") as fp:
        # Save address as hex
        address = hex_address(address)
        if alias is not None:
            logging.info(f"📦 Registering deployment as {alias} in {file}")
        else:
            logging.info(f"📦 Registering {address} in {file}")

        fp.write(f"{address}:{abi}")
        if alias is not None:
            fp.write(f":{alias}")
        fp.write("\n")


def update(address_or_alias, abi, network):
    """Update the ABI for an existing deployment."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        raise Exception(f"{file} does not exist")

    with open(file, "r") as fp:
        lines = fp.readlines()

    as_address = None
    try:
        as_address = normalize_number(address_or_alias)
    except ValueError:
        pass

    found = False
    for i in range(len(lines)):
        line = lines[i].strip().split(":")

        current_address = line[0]

        current_alias = None
        if len(line) > 2:
            current_alias = line[2]

        if address_or_alias == current_alias or (
            as_address is not None and as_address == normalize_number(current_address)
        ):
            logging.info(f"📦 Updating deployment {address_or_alias} in {file}")

            replacement = f"{current_address}:{abi}"
            if current_alias is not None:
                replacement += f":{current_alias}"
            replacement += "\n"

            lines[i] = replacement

            found = True
            break

    if not found:
        raise Exception(
            f"Deployment with address or alias {address_or_alias} does not exist in {file}"
        )
    else:
        with open(file, "w+") as fp:
            fp.writelines(lines)


def register_class_hash(hash, network, alias):
    """Register a new deployment."""
    file = f"{network}.{DECLARATIONS_FILENAME}"

    if class_hash_exists(hash, network):
        raise Exception(f"Hash {hash[:6]}...{hash[-6:]} already exists in {file}")

    with open(file, "a") as fp:
        # Save class_hash as hex
        hash = hex(hash)
        if alias is not None:
            logging.info(f"📦 Registering {alias} in {file}")
        else:
            logging.info(f"📦 Registering {hash} in {file}")

        fp.write(f"{hash}")
        if alias is not None:
            fp.write(f":{alias}")
        fp.write("\n")


def exists(address_or_alias, network):
    """
    Return whether a deployment exists or not.

    If address_or_alias is an int, address is assumed.

    If address_or_alias is a str, alias is assumed.
    """
    deployment = next(load(address_or_alias, network), None)
    return deployment is not None


def class_hash_exists(hash, network):
    """Return whether a class declaration exists or not."""
    if hash in load_class(hash, network):
        return True


def load(address_or_alias, network):
    """
    Load deployments that matches an identifier (address or alias).

    If address_or_alias is an int, address is assumed.

    If address_or_alias is a str, alias is assumed.
    """
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        return

    with open(file) as fp:
        for line in fp:
            [address, abi, *alias] = line.strip().split(":")
            address = normalize_number(address)
            identifiers = [address]
            if type(address_or_alias) is not int:
                identifiers = alias
            if address_or_alias in identifiers:
                yield address, abi


def load_class(hash_or_alias, network):
    """
    Load declaration class that matches an identifier (hash or alias).

    If hash_or_alias is an int, class_hash is assumed.

    If hash_or_alias is a str, alias is assumed.
    """
    file = f"{network}.{DECLARATIONS_FILENAME}"

    if not os.path.exists(file):
        return

    with open(file) as fp:
        for line in fp:
            [hash, *alias] = line.strip().split(":")
            hash = normalize_number(hash)
            identifiers = [hash]
            if type(hash_or_alias) is not int:
                identifiers = alias
            if hash_or_alias in identifiers:
                yield hash
