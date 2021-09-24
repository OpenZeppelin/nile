import os
import shutil
import subprocess
import sys
import urllib

from nile.constants import TEMP_DIRECTORY

def install_command(tag):
  url = f"https://github.com/starkware-libs/cairo-lang/releases/download/v{tag}/cairo-lang-{tag}.zip"
  location = f"{TEMP_DIRECTORY}cairo-lang-{tag}.zip"
  os.makedirs(TEMP_DIRECTORY, exist_ok=True)
  urllib.request.urlretrieve(url, location)
  subprocess.check_call([sys.executable, "-m", "pip", "install", location])
  shutil.rmtree(TEMP_DIRECTORY)