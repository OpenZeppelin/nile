"""Command to clean artifacts from workspace."""
import logging
import os
import shutil

from nile.common import (
    ACCOUNTS_FILENAME,
    BUILD_DIRECTORY,
    DECLARATIONS_FILENAME,
    DEPLOYMENTS_FILENAME,
)


def clean():
    """Remove artifacts from workspace."""
    local_files = [
        f"localhost.{DEPLOYMENTS_FILENAME}",
        f"localhost.{DECLARATIONS_FILENAME}",
        f"localhost.{ACCOUNTS_FILENAME}",
        BUILD_DIRECTORY,
    ]

    for file in local_files:
        if os.path.exists(file):
            logging.info(f"🚮 Deleting {file}")

            if file is BUILD_DIRECTORY:
                shutil.rmtree(BUILD_DIRECTORY)
            else:
                os.remove(file)

    logging.info("✨ Workspace clean, keep going!")
