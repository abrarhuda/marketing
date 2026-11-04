# GitHub Actions workflows

This folder contains automated checks that run on GitHub:

- `ci.yml` installs the project dependencies.
- `ci.yml` runs the 25-test pytest suite.
- `ci.yml` runs Ruff linting.

The workflow runs automatically on pushes to `main` and pull requests. It can
also be started manually from the repository's **Actions** tab through the
`workflow_dispatch` trigger.
