# Contributing to OpenZeppelin Nile

We really appreciate and value contributions to OpenZeppelin Nile. Please take 5' to review the items listed below to make sure that your contributions are merged as soon as possible.

## Contribution guidelines

Before starting development, please [create an issue](https://github.com/OpenZeppelin/nile/issues/new) to open the discussion, validate that the PR is wanted, and coordinate overall implementation details.

And make sure to always include tests and documentation for the new developments.

## Creating Pull Requests (PRs)

As a contributor, you are expected to fork this repository, work on your own fork and then submit pull requests. The pull requests will be reviewed and eventually merged into the main repo. See ["Fork-a-Repo"](https://help.github.com/articles/fork-a-repo/) for how this works.

## A typical workflow

1. Make sure your fork is up to date with the main repository:

    ```sh
    cd nile
    git remote add upstream https://github.com/OpenZeppelin/nile.git
    git fetch upstream
    git pull --rebase upstream main
    ```

    > NOTE: The directory `nile` represents your fork's local copy.

2. Branch out from `main` into `fix/some-bug-#123`:

    (Postfixing #123 will associate your PR with the issue #123 and make everyone's life easier =D)

    ```sh
    git checkout -b fix/some-bug-#123
    ```

3. Make your changes and run tests, linter, etc. This can be done by running local continuous integration and make sure it passes.

    ```bash
    tox
    tox -e format
    tox -e lint
    ```

4. Add your files, commit, and push to your fork.

    ```sh
    git add some_file.py
    git commit "Fix some bug #123"
    git push origin fix/some-bug-#123
    ```

5. Go to [github.com/OpenZeppelin/nile](https://github.com/OpenZeppelin/nile) in your web browser and issue a new pull request.
    Begin the body of the PR with "Fixes #123" or "Resolves #123" to link the PR to the issue that it is resolving.
    *IMPORTANT* Read the PR template very carefully and make sure to follow all the instructions. These instructions
    refer to some very important conditions that your PR must meet in order to be accepted, such as making sure that all PR checks pass.

6. Maintainers will review your code and possibly ask for changes before your code is pulled into the main repository. We'll check that all tests pass, review the coding style, and check for general code correctness. If everything is OK, we'll merge your pull request and your code will be part of OpenZeppelin Nile.

    *IMPORTANT* Please pay attention to the maintainer's feedback, since it's a necessary step to keep up with the standards OpenZeppelin Nile attains to.


## Design Patterns

We always try to follow best practices and design patterns to make the code readable and maintainable. While most of them are left to be decided by the PR developer and the reviewer, we require following some patterns that we enforce ourselves which are presented below:

### Hex/Int pattern

The pattern is defined as follows:

#### Definitions
- **Internal API** is the set of functions that are not meant to be called directly in scripting, tests, or any other context from users of Nile, but only internally from other Nile code (including plugins).
- **Public API** is the complement.

#### Rules
- Accept and use **only int for Internal API** (for hashes, keys, or addresses).
- Accept **both hex and int from external input** (config files, starknet cli output, etc.) **or Public API functions**, and convert the input to int before using it internally (use `nile.utils.normalize_number`).
- Always **return int from Internal or Public API, except when the method explicitly declares the intention to return a hex** (like `nile.utils.hex_class_hash` helper).
- Convert to **hex before logging into files or CLI** (like in address for accounts or class_hash for declares) to keep consistency.
- Convert to **hex when required for integrations** (like starknet cli subprocess calls), **right before where it is needed**.


## All set

If you have any questions, feel free to post them to github.com/OpenZeppelin/nile/issues.

Finally, if you're looking to collaborate and want to find easy tasks to start, look at the issues we marked as ["Good first issue"](https://github.com/OpenZeppelin/nile/labels/good%20first%20issue).

Thanks for your time and code!
