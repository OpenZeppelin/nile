"""Command to install a specific version of Cairo."""
from pathlib import Path
import sys, subprocess
import urllib.request
import shutil

from nile.common import TEMP_DIRECTORY


def install_command(tag):
    """Install Cairo package with the given tag."""
    print(f"🗄  Installing Cairo v{tag}")
    url = f"https://github.com/starkware-libs/cairo-lang/releases/download/v{tag}/cairo-lang-{tag}.zip"  # noqa: E501
    location = f"{TEMP_DIRECTORY}cairo-lang-{tag}.zip"
    Path(TEMP_DIRECTORY).mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, location)
    subprocess.check_call([sys.executable, "-m", "pip", "install", location])
    shutil.rmtree(TEMP_DIRECTORY)
    print(f"✨  Cairo v{tag} successfully installed!")
