import os
import subprocess

from nile.constants import get_all_contracts, ABIS_DIRECTORY, CONTRACTS_DIRECTORY, BUILD_DIRECTORY

def compile_command(contracts):
  # to do: automatically support subdirectories

  if not os.path.exists(ABIS_DIRECTORY):
    print(f"Creating {ABIS_DIRECTORY} to store compilation artifacts")
    os.makedirs(ABIS_DIRECTORY, exist_ok=True)

  if len(contracts) == 0:
    print(f"🤖 Compiling all Cairo contracts in the {CONTRACTS_DIRECTORY} directory")
    for path in get_all_contracts():
      compile_contract(path)
  elif len(contracts) == 1:
    compile_contract(contracts[0])
  else:
    for path in contracts:
      compile_contract(path)
  
  print("✅ Done")


def compile_contract(path):
  base = os.path.basename(path)
  filename = os.path.splitext(base)[0]
  print(f"🔨 Compiling {path}")

  cmd = f"""
  starknet-compile {path} \
    --cairo_path={CONTRACTS_DIRECTORY}
    --output {BUILD_DIRECTORY}{filename}.json \
    --abi {ABIS_DIRECTORY}{filename}.json
  """
  process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
  output, error = process.communicate()
