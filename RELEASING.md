# Releasing

Releasing checklist:

(1) Write a changelog.

(2) Checkout the `main` branch. This is the only releasable branch.

(3) Update the version in `docs/antora.yml`, create a PR, and wait for it to be merged.

(4) Create a tag for the release.

```sh
git tag v0.8.0
```

(5) Push the tag to the main repository, [triggering the CI and release process](https://github.com/OpenZeppelin/nile/blob/951cf2403aa58a9b58c3c1a793b51cd5c58cb56e/.github/workflows/ci.yml#L55).

```sh
git push origin v0.8.0
```

(6) Finally, go to the repo's [releases page](https://github.com/OpenZeppelin/nile/releases/) and [create a new one](https://github.com/OpenZeppelin/nile/releases/new) with the new tag and the `main` branch as target.
