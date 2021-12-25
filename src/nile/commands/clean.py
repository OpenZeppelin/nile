"""Command to clean artifacts from workspace."""
import os
import shutil

from nile.common import (
    ACCOUNTS_FILENAME,
    BUILD_DIRECTORY,
    DEPLOYMENTS_FILENAME,
)


def clean_command():
    """Remove artifacts from workspace."""
    local_deployments_filename = f"localhost.{DEPLOYMENTS_FILENAME}"
    local_accounts_filename = f"localhost.{ACCOUNTS_FILENAME}"

    if os.path.exists(local_deployments_filename):
        print(f"🚮 Deleting {local_deployments_filename}")
        os.remove(local_deployments_filename)

    if os.path.exists(local_accounts_filename):
        print(f"🚮 Deleting {local_accounts_filename}")
        os.remove(local_accounts_filename)

    if os.path.exists(BUILD_DIRECTORY):
        print(f"🚮 Deleting {BUILD_DIRECTORY} directory")
        shutil.rmtree(BUILD_DIRECTORY)
    print("✨ Workspace clean, keep going!")
