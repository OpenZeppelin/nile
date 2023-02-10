"""Cairo1 common."""

from pathlib import Path

COMPILERS_BIN_PATH = Path(__file__).parent / "./compilers/src/bin"
BUILD_DIRECTORY = "artifacts/cairo1"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
