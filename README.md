# ⛵ Nile

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
This command creates the project directory structure and installs `cairo-lang`, `pytest`, and `pytest-asyncio` for you. The template includes a makefile to build the project (`make build`) and run tests (`make test`).

## Usage
### `compile`

Compile Cairo contracts. Compilation articacts are written into the `artifacts/` directory.

```sh
nile compile # compiles all contracts under contracts/
nile compile contracts/MyContract.cairo # compiles single contract
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

### `clean`
Deletes the `artifacts/` directory for a fresh start ❄️

```sh
nile clean
```

### `install`
Install the latest version of the Cairo language

```sh
nile install
```

### `version`
Print out the Nile version

```sh
nile version
```

## Hacking on Nile

Nile uses tox to manage development tasks, you can get a list of
available task with `tox -av`.

 * Install a development version of the package with `python -m pip install .`
 * Run tests with `tox`
 * Build the package with `tox -e build`
 * Format all files with `tox -e format`
 * Check files formatting with `tox -e lint`


## License
Nile is released under the MIT License.
