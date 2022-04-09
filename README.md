[![Tests and linter](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml)
# OpenZeppelin Nile ⛵

_Navigate your [StarkNet](https://www.cairo-lang.org/docs/hello_starknet/index.html) projects written in [Cairo](https://cairo-lang.org)._

## Getting started

Create a folder for your project and `cd` into it:
```sh
mkdir myproject
cd myproject
```

Create a [virtualenv](https://docs.python.org/3/library/venv.html) and activate it:

```sh
python3 -m venv env
source env/bin/activate
```

Install `nile`:

```sh
pip install cairo-nile
```

Use `nile` to quickly set up your development environment:

```sh
nile init
...
✨  Cairo successfully installed!
...
✅ Dependencies successfully installed
🗄  Creating project directory tree
⛵️ Nile project ready! Try running:
```
This command creates the project directory structure and installs `cairo-lang`, `starknet-devnet`, `pytest`, and `pytest-asyncio` for you. The template includes a makefile to build the project (`make build`) and run tests (`make test`).

## Usage
### `node`

Run a local [`starknet-devnet`](https://github.com/Shard-Labs/starknet-devnet/) node:

```sh
nile node

 * Serving Flask app 'starknet_devnet.server' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

### `compile`

Compile Cairo contracts. Compilation artifacts are written into the `artifacts/` directory.

```sh
nile compile # compiles all contracts under contracts/
nile compile --directory my_contracts # compiles all contracts under my_contracts/
nile compile contracts/MyContract.cairo # compiles single contract
nile compile contracts/MyContract.cairo --disable-hint-validation # compiles single contract with unwhitelisted hints
```

As of cairo-lang v0.8.0, account contracts (contracts with the `__execute__` method) must be compiled with the `--account_contract` flag.

```sh
nile compile contracts/MyAccount.cairo --account_contract # compiles account contract
```

Example output:
```
$ nile compile
Creating artifacts/abis/ to store compilation artifacts
🤖 Compiling all Cairo contracts in the contracts/ directory
🔨 Compiling contracts/Account.cairo
🔨 Compiling contracts/Initializable.cairo
🔨 Compiling contracts/Ownable.cairo
✅ Done
```

### `deploy`
```sh
nile deploy contract --alias my_contract

🚀 Deploying contract
🌕 artifacts/contract.json successfully deployed to 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
📦 Registering deployment as my_contract in localhost.deployments.txt
```

A few things to notice here:

1. `nile deploy <contract_name>` looks for an artifact with the same name
2. This created a `localhost.deployments.txt` file storing all data related to my deployment
3. The `--alias` parameter lets me create an unique identifier for future interactions, if no alias is set then the contract's address can be used as identifier
4. By default Nile works on local, but you can use the `--network` parameter to interact with `mainnet`, `goerli`, and the default `localhost`.

### `setup`
Deploy an Account associated with a given private key.

To avoid accidentally leaking private keys, this command takes an alias instead of the actual private key. This alias is associated with an environmental variable of the same name, whose value is the actual private key.

You can find an example `.env` file in `example.env`. These are private keys only to be used for testing and never in production.

```sh
nile setup <private_key_alias>

🚀 Deploying Account
🌕 artifacts/Account.json successfully deployed to 0x07db6b52c8ab888183277bc6411c400136fe566c0eebfb96fffa559b2e60e794
📦 Registering deployment as account-0 in localhost.deployments.txt
Invoke transaction was sent.
Contract address: 0x07db6b52c8ab888183277bc6411c400136fe566c0eebfb96fffa559b2e60e794
Transaction hash: 0x17
```

A few things to notice here:

1. `nile setup <private_key_alias>` looks for an environment variable with the name of the private key alias
2. This creates a `localhost.accounts.json` file storing all data related to accounts management

### `send`
Execute a transaction through the `Account` associated with the private key provided. The syntax is:

```sh
nile send <private_key_alias> <contract_identifier> <method> [PARAM_1, PARAM2...]
```

For example:
```sh
nile send <private_key_alias> ownable0 transfer_ownership 0x07db6...60e794

Invoke transaction was sent.
Contract address: 0x07db6b52c8ab888183277bc6411c400136fe566c0eebfb96fffa559b2e60e794
Transaction hash: 0x1c
```

### `call` and `invoke`
Using `call` and `invoke`, we can perform read and write operations against our local node (or public one using the `--network mainnet` parameter). The syntax is:

```
nile <command> <contract_identifier> <method> [PARAM_1, PARAM2...]
```

Where `<command>` is either `call` or `invoke` and `<contract_identifier>` is either our contract address or alias, as defined on `deploy`.

```sh
nile invoke my_contract increase_balance 1

Invoke transaction was sent.
Contract address: 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
Transaction hash: 0x1
```

```sh
nile call my_contract get_balance

1
```

### `run`
Execute a script in the context of Nile. The script must implement a `run(nre)` function to receive a `NileRuntimeEnvironment` object exposing Nile's scripting API.

```python
# path/to/script.py

def run(nre):
    address, abi = nre.deploy("contract", alias="my_contract")
    print(abi, address)
```

Then run the script:

```sh
nile run path/to/script.py
```

### `clean`
Deletes the `artifacts/` directory for a fresh start ❄️

```sh
nile clean

🚮 Deleting localhost.deployments.txt
🚮 Deleting artifacts directory
✨ Workspace clean, keep going!
```

### `install`
Install the latest version of the Cairo language and the starknet-devnet local node.

```sh
nile install
```

### `version`
Print out the Nile version

```sh
nile version
```

### `debug`
Use locally available contracts to make error messages from rejected transactions more explicit.  

```sh
nile debug <transaction_hash> [CONTRACTS_FILE, NETWORK]
```

For example, this transaction returns the very cryptic error message:  
`An ASSERT_EQ instruction failed: 0 != 1.`

```sh
starknet tx_status \
  --hash 0x57d2d844923f9fe5ef54ed7084df61f926b9a2a24eb5d7e46c8f6dbcd4baafe \
  --error_message

[...]
Error in the called contract (0x5bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4):
Error at pc=0:1360:
An ASSERT_EQ instruction failed: 0 != 1.
Cairo traceback (most recent call last):
Unknown location (pc=0:1384)
Unknown location (pc=0:1369)
```

This can be made more explicit with:

```sh
nile debug 0x57d2d844923f9fe5ef54ed7084df61f926b9a2a24eb5d7e46c8f6dbcd4baafe

⏳ Querying the network to check transaction status and identify contracts...
🧾 Found contracts: ['0x05bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4:artifacts/Evaluator.json']
⏳ Querying the network with contracts...
🧾 Error message:

[...]
Error in the called contract (0x5bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4):
[path_to_file]:179:5: Error at pc=0:1360:
    assert permission = 1
    ^*******************^
An ASSERT_EQ instruction failed: 0 != 1.
Cairo traceback (most recent call last):
[path_to_file]:184:6
func set_teacher{
     ^*********^
[path_to_file]:189:5
    only_teacher()
    ^************^
```

In case of pending transaction states, the command will offer to continue probing the network unless it
is terminated prematurely.
This example also shows how accepted transactions are handled.

```sh
⏳ Querying the network to check transaction status and identify contracts...
🕒 Transaction status: NOT_RECEIVED. Trying again in a moment...
🕒 Transaction status: RECEIVED. Trying again in a moment...
🕒 Transaction status: PENDING. Trying again in a moment...
✅ Transaction status: ACCEPTED_ON_L2. No error in transaction.
```

Finally, the command will use the local `network.deployments.txt` files to fetch the available contracts.  
However, it is also possible to override this by passing a `CONTRACTS_FILE` argument, formatted as
```
CONTRACT_ADDRESS1:PATH_TO_COMPILED_CONTRACT1.json
CONTRACT_ADDRESS2:PATH_TO_COMPILED_CONTRACT2.json
...
```

## Extending Nile with plugins

Nile has the possibility of extending its CLI and `NileRuntimeEnvironment` functionalities through plugins. For developing plugins for Nile fork [this plugin example](https://github.com/franalgaba/nile-plugin-example) boilerplate and implement your desired functionality with the provided instructions.

### How it works

This implementation takes advantage of the native extensibility features of [click](https://click.palletsprojects.com/). Using click and leveraging the Python [entrypoints](https://packaging.python.org/en/latest/specifications/entry-points/) we have a simple manner of handling extension natively on Python environments through dependencies. The plugin implementation on Nile looks for specific Python entrypoints constraints for adding commands.

In order for this implementation to be functional, it is needed by the plugin developer to follow some development guidelines defined in this simple plugin example extending Nile for a dummy greet extension. In a brief explanation the guidelines are as follows:

1. Define a Python module that implement a click command or group:

```python
# First, import click dependency
import click

# Decorate the method that will be the command name with `click.command` 
@click.command()
# You can define custom parameters as defined in `click`: https://click.palletsprojects.com/en/7.x/options/
def my_command():
    # Help message to show with the command
    """
    Subcommand plugin that does something.
    """
    # Done! Now implement your custom functionality in the command
    click.echo("I'm a plugin overiding a command!")
```

2. Define the plugin entrypoint. In this case using Poetry features in the pyproject.toml file:

```
# We need to specify that click commands are Poetry entrypoints of type `nile_plugins`. Do not modify this
[tool.poetry.plugins."nile_plugins"]
# Here you specify you command name and location <command_name> = <package_method_location>
"greet" = "nile_greet.main.greet"
```

3. Done!

How to decide if I want to use a plugin or not? Just install / uninstall the plugin dependency from your project :smile:

Finally, after the desired plugin is installed, it will also be automatically available through the `nre`. The plugin developer should be aware of this and design the interface accordingly.

## Hacking on Nile

Nile uses tox to manage development tasks, you can get a list of
available task with `tox -av`.

 * Install a development version of the package with `python -m pip install .`
 * Build the package with `tox -e build`
 * Format all files with `tox -e format`
 * Check files formatting with `tox -e lint`

### Testing

To run tests:
 * Install testing dependencies with `python -m pip install .[testing]`
 * Run all tests with `tox`
 * Run unit tests only with `tox -e unit`
 * To run a specific set of tests, point to a module and/or function, e.g. `tox tests/test_module.py::test_function`
 * Other `pytest` flags must be preceded by `--`, e.g. `tox -- --pdb` to run tests in debug mode

## License
Nile is released under the MIT License.
