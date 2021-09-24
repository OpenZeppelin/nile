# ⛵ Nile

_Navigate your [StarkNet](https://www.cairo-lang.org/docs/hello_starknet/index.html) projects written in [Cairo](cairo-lang.org)._

## Installation

```sh
pip install cairo-nile
```

## Usage

### Install Cairo

Use `nile` to install a given version of the Cairo language. Given Cairo's fast development pace, this command is useful to install the latest version.

```sh
nile install 0.4.0
```

### Compile

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

### Clean

Deletes the `artifacts/` directory for a fresh start ❄️

```
nile clean
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
