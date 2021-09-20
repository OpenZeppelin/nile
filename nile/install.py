#!/usr/bin/env python
import sys, os, shutil, subprocess
import urllib.request
from config import TEMP_DIRECTORY

def install(tag):
  url = f"https://github.com/starkware-libs/cairo-lang/releases/download/v{tag}/cairo-lang-{tag}.zip"
  location = f"{TEMP_DIRECTORY}cairo-lang-{tag}.zip"
  os.makedirs(TEMP_DIRECTORY, exist_ok=True)
  urllib.request.urlretrieve(url, location)
  subprocess.check_call([sys.executable, "-m", "pip", "install", location])
  shutil.rmtree(TEMP_DIRECTORY)

if __name__ == "__main__":
  if len(sys.argv) == 2:
    install(sys.argv[1])
  else:
    print("Please provide a valid Cairo language version. For example:")
    print("")
    print("nile install 0.4.0")
    print("")
