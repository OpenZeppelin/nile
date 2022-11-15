"""nile common module."""
import logging
import os

from nile.common import DECLARATIONS_FILENAME, DEPLOYMENTS_FILENAME
from nile.utils import hex_address, hex_class_hash, normalize_number


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


def unregister(address_or_class_hash, network, alias, abi=None, is_declaration=False):
    """Unregister deployment or class hash from file."""
    file = (
        f"{network}.{DECLARATIONS_FILENAME}"
        if is_declaration
        else f"{network}.{DEPLOYMENTS_FILENAME}"
    )
    to_delete = (
        hex_class_hash(address_or_class_hash)
        if is_declaration
        else hex_address(address_or_class_hash)
    )

    if abi is not None:
        to_delete = f"{to_delete}:{abi}"

    if alias:
        to_delete = f"{to_delete}:{alias}"

    with open(file, "r") as fp:
        lines = fp.readlines()
        with open(file, "w") as new_fp:
            for line in lines:
                if not line.startswith(to_delete):
                    new_fp.write(line)


def update_abi(address_or_alias, abi, network):
    """
    Update the ABI for an existing deployment that matches an identifier.

    If address_or_alias is an int, address is assumed.

    If address_or_alias is a str, alias is assumed.
    """
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        raise Exception(f"{file} does not exist")

    with open(file, "r") as fp:
        lines = fp.readlines()

    found = False
    for i in range(len(lines)):
        [address, current_abi, *aliases] = lines[i].strip().split(":")
        address = normalize_number(address)
        identifiers = [address]

        if type(address_or_alias) is not int:
            identifiers = aliases

        if address_or_alias in identifiers:
            # Save address as hex
            address = hex_address(address)

            identifier = address_or_alias
            if type(address_or_alias) is int:
                identifier = address
            logging.info(f"📦 Updating {identifier} in {file}")

            replacement = f"{address}:{abi}"
            if len(aliases) > 0:
                replacement += ":" + ":".join(str(x) for x in aliases)
            replacement += "\n"
            lines[i] = replacement
            found = True
            break

    if not found:
        raise Exception(f"Deployment {address_or_alias} does not exist in {file}")
    else:
        with open(file, "w+") as fp:
            fp.writelines(lines)


def register_class_hash(hash, network, alias):
    """Register a new deployment."""
    file = f"{network}.{DECLARATIONS_FILENAME}"

    padded_hash = hex_class_hash(hash)

    if class_hash_exists(hash, network):
        raise Exception(
            f"Hash {padded_hash[:6]}...{padded_hash[-6:]} already exists in {file}"
        )

    with open(file, "a") as fp:
        if alias is not None:
            logging.info(f"📦 Registering {alias} in {file}")
        else:
            logging.info(f"📦 Registering {padded_hash} in {file}")

        fp.write(f"{padded_hash}")
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
