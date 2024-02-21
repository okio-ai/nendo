# Contributing

Nendo is a collaborative effort and we greatly appreciate any and all contributions and will always give credit to the authors.

## Development environment setup

It's super easy to get started with the nendo development environment. Just make sure you are using a supported version of python (`3.8`, `3.9` or `3.10`) and run the following command from your `nendo/` directory:

```bash
make setup
```

> **Note**:
> Developing for and with Nendo Core requires careful dependency management. The use of a [python virtual environment](https://docs.python.org/3/library/venv.html) like [pyenv](https://github.com/pyenv/pyenv) or [poetry](https://python-poetry.org/) is highly recommended.

## Development process

To start writing code, proceed as follows:

1. create a new branch: `git checkout -b feature/feature-name`
    1. For branches introducing new features, please use the `feauture/` prefix for your branch.
    2. For branches submitting buxfixes, please use the `fix/` prefix for your branch.
1. edit the code and/or the documentation

**Before submitting a PR for review:**

1. run `make format` to auto-format the code
1. run `make check` to check everything (then fix any warning)
1. run `make test` to run the tests (then fix any issue)
1. if you updated the documentation or the project dependencies:
    1. run `make docs`
    1. go to http://localhost:8000 and check that everything looks good
1. Once everything is looking smooth, create your Pull Request on github

## Using poetry

If you want to use poetry:

1. [Install poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
1. `git clone git@github.com:okio-ai/nendo.git`
1. `cd nendo`
1. `make setup-poetry`

Remember to also prepend `poetry run` to all `make` commands in order for them to work.