# Contributing

This package is open to contributions 👏

To contribute, please follow these steps:

1. Fork the upstream repository into a personal account.
2. Install [uv](https://docs.astral.sh/uv/), then install all dependencies with ``uv sync --all-extras --group dev``
3. Install [prek](https://prek.j178.dev/) (for project linting) by running ``prek install`` (or ``prek install -f`` if you previously ran ``pre-commit install``)
4. Create a new branch for your changes, and make sure to add tests!
5. Push the topic branch to your personal fork
6. Run `prek run --all-files` locally to ensure proper linting
7. Create a pull request to the snok repository with a detailed summary of your changes and what motivated the change
