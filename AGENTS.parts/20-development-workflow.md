## Development workflow

`multi` uses **trunk-based development**. `main` is the only long-lived branch —
commit and push directly to `main`. There is no `staging` branch and no
PR-based integration branch; do not create one.

Every push to `main` runs the Auto Version workflow, which tags the next patch
release and publishes to PyPI, so keep `main` releasable.
