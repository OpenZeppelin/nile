"""nile common module."""
import logging
import os

from nile.common import DECLARATIONS_FILENAME, DEPLOYMENTS_FILENAME


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


def update(address, abi, network, alias):
    """Update a deployment at an existing address."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        raise Exception(f"{file} does not exist")

    if alias is not None:
        if exists(alias, network):
            raise Exception(f"Alias {alias} already exists in {file}")

    with open(file, "r") as fp:
        lines = fp.readlines()

    found = False
    for i in range(len(lines)):
        line = lines[i].strip().split(":")
        current_address = line[0]

        new_alias = alias
        if new_alias is None and len(line) > 2:
            new_alias = line[2]

        if current_address == address:
            found = True

            replacement = f"{address}:{abi}"
            if new_alias is not None:
                logging.info(f"📦 Updating deployment as {new_alias} in {file}")
                replacement += f":{new_alias}"
            else:
                logging.info(f"📦 Updating {address} in {file}")
            replacement += "\n"

            lines[i] = replacement

    if not found:
        raise Exception(f"Address {address} does not exist in {file}")
    else:
        with open(file, "w+") as fp:
            fp.writelines(lines)


def register_class_hash(hash, network, alias):
    """Register a new deployment."""
    file = f"{network}.{DECLARATIONS_FILENAME}"

    if class_hash_exists(hash, network):
        raise Exception(f"Hash {hash[:6]}...{hash[-6:]} already exists in {file}")

    with open(file, "a") as fp:
        if alias is not None:
            logging.info(f"📦 Registering {alias} in {file}")
        else:
            logging.info(f"📦 Registering {hash} in {file}")

        fp.write(f"{hash}")
        if alias is not None:
            fp.write(f":{alias}")
        fp.write("\n")


def exists(identifier, network):
    """Return whether a deployment exists or not."""
    foo = next(load(identifier, network), None)
    return foo is not None


def class_hash_exists(hash, network):
    """Return whether a class declaration exists or not."""
    if hash in load_class(hash, network):
        return True


def load(identifier, network):
    """Load deployments that matches an identifier (address or alias)."""
    file = f"{network}.{DEPLOYMENTS_FILENAME}"

    if not os.path.exists(file):
        return

    with open(file) as fp:
        for line in fp:
            [address, abi, *alias] = line.strip().split(":")
            identifiers = [x for x in [address] + alias]
            if identifier in identifiers:
                yield address, abi


def load_class(identifier, network):
    """Load declaration class that matches an identifier (hash or alias)."""
    file = f"{network}.{DECLARATIONS_FILENAME}"

    if not os.path.exists(file):
        return

    with open(file) as fp:
        for line in fp:
            [hash, *alias] = line.strip().split(":")
            identifiers = [x for x in [hash] + alias]
            if identifier in identifiers:
                yield hash
