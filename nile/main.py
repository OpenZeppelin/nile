#!/usr/bin/env python
import sys, os, shutil, subprocess
import urllib.request
import click

CONTRACTS_DIRECTORY = "contracts/"
BUILD_DIRECTORY = "artifacts/"
TEMP_DIRECTORY = ".temp/"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}abis/"

@click.group()
def cli():
  pass


@cli.command()
@click.argument('tag')
def install(tag):
  """Install TAG version of Cairo"""
  url = f"https://github.com/starkware-libs/cairo-lang/releases/download/v{tag}/cairo-lang-{tag}.zip"
  location = f"{TEMP_DIRECTORY}cairo-lang-{tag}.zip"
  os.makedirs(TEMP_DIRECTORY, exist_ok=True)
  urllib.request.urlretrieve(url, location)
  subprocess.check_call([sys.executable, "-m", "pip", "install", location])
  shutil.rmtree(TEMP_DIRECTORY)


@cli.command()
@click.argument('contracts', nargs=-1)
def compile(contracts):
  """
  $ compile.py 
    Compiles all contracts in CONTRACTS_DIRECTORY

  $ compile.py contracts/MyContract.cairo
    Compiles MyContract.cairo

  $ compile.py contracts/foo.cairo contracts/bar.cairo
    Compiles foo.cairo and bar.cairo
  """

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


def get_all_contracts():
  for filename in os.listdir(CONTRACTS_DIRECTORY):
    if filename.endswith(".cairo"):
        yield os.path.join(CONTRACTS_DIRECTORY, filename)


@cli.command()
def clean():
  shutil.rmtree(BUILD_DIRECTORY)


if __name__ == '__main__':
  cli()
