from pathlib import Path
import shutil
import dataclasses

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, TextColumn, BarColumn

console = Console()


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-").lower()


def to_class_name(string: str) -> str:
    string = string.replace("nendo_plugin_", "")
    return "".join([w.capitalize() for w in string.split("_")])


def create_test_py(plugin_name: str, class_name: str) -> str:
    return f"""from nendo import Nendo, NendoConfig, NendoTrack
import unittest

nd = Nendo(
    config=NendoConfig(
        log_level="INFO",
        plugins=["{plugin_name}"],
    ),
)


class {class_name}Tests(unittest.TestCase):
    def test_run_{plugin_name.replace("nendo_plugin_", "")}(self):
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        track = nd.plugins.{plugin_name.replace("nendo_plugin_", "")}(track=track)
        self.assertEqual(type(track), NendoTrack)


if __name__ == "__main__":
    unittest.main()
    """


def create_setup_py(plugin_name: str, description: str, author: str) -> str:
    return f"""from distutils.core import setup

if __name__ == "__main__":
    setup(
        name="{to_kebab_case(plugin_name)}",
        version="0.1.0",
        description="{description}",
        author="{author}",
    )
    
    """


def create_init_py(class_name: str) -> str:
    return f"""from __future__ import annotations

from .plugin import {class_name}

__version__ = "0.1.0"

__all__ = [
    "{class_name}",
]

    """


def create_config_py(class_name: str) -> str:
    return f"""from nendo import NendoConfig
from pydantic import Field

class {class_name}(NendoConfig):
    my_default_param: str = Field("my_default_value")

    """


def create_plugin_py(plugin_type: str, class_name: str, config_class_name: str) -> str:
    if plugin_type == "AnalysisPlugin":
        return_type = "None"
        method_body = "pass"
    else:
        return_type = "NendoTrack"
        method_body = "return track"
    return f"""from nendo import Nendo, {plugin_type}, NendoConfig, NendoTrack
from .config import {config_class_name}

settings = {config_class_name}()

class {class_name}({plugin_type}):
    nendo_instance: Nendo = None
    config: NendoConfig = None

    @{plugin_type}.run_track
    def run_plugin(self, track: NendoTrack) -> {return_type}:
        {method_body}

        """


def create_mkdocs_yml(plugin_name: str) -> str:
    return f"""
site_name: {plugin_name}

nav:
    - "index.md"
    - Example Page: "example.md"

    """


def create_readme_md(plugin_name: str, description: str, author: str) -> str:
    return f"""# {plugin_name}

![Documentation](https://img.shields.io/website/https/nendo.ai)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/okio_ai.svg?style=social&label=Follow%20%40okio_ai)](https://twitter.com/okio_ai) [![](https://dcbadge.vercel.app/api/server/gaZMZKzScj?compact=true&style=flat)](https://discord.gg/gaZMZKzScj)

Created by {author}

## Description
{description}

## Installation
```bash
pip install {to_kebab_case(plugin_name)}
```

## Usage
```pycon
>>> from nendo import Nendo
>>> nd = Nendo(plugins=["{plugin_name}"])
>>> track = nd.library.add_track(file_path="path/to/file.mp3")

>>> track = nd.plugins.{plugin_name.replace("nendo_plugin_", "")}(track=track)
>>> track.play()
```

    """


def create_success_message(
    author_name: str, plugin_name: str, folder: str, plugin_path: Path
) -> Markdown:
    return Markdown(
        f"""# All done!
Thanks for all the infos {author_name}. 
We've created your plugin `{plugin_name}` at [{folder}]({folder}).

Now you can install your plugin with: 
```sh
cd {plugin_path}
pip install -e .
pytest tests
```

Be sure to check out the nendo documentation at [https://okio.ai/docs/]([https://okio.ai/docs/]).

        """
    )


def create_pyproject_toml(plugin_name: str, author: str, description: str) -> str:
    return f"""[tool.poetry]
name = "{to_kebab_case(plugin_name)}"
version = "0.1.0"
authors = [
    "{author}",
]
description = "{description}"
license = "MIT"
readme = "README.md"
repository = "https://github.com/{author}/{plugin_name}"
homepage = "https://nendo.ai"
keywords = [
    "AI",
    "generative",
    "music",
    "okio",
    "nendo",
    "music production",
    "music generation",
    "music information retrieval",
    "MIR",
    "music analysis",
    "song analysis",
]
classifiers = [
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Multimedia :: Sound/Audio",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]

[tool.poetry.dependencies]
python = "^3.8,<3.11"
nendo = "^0.1.0"
pydantic = "^2.4.2"

[tool.ruff]
target-version = "py38"
# Same as Black.
line-length = 88
src = ["src"]
select = [
    "A",
    # "ANN", # flake8-annotations
    "ARG",
    "B",
    "BLE",
    "C",
    "C4",
    "COM",
    "D",
    "DTZ",
    "E",
    "ERA",
    "EXE",
    "F",
    # "FBT", # flake8-boolean-trap
    "G",
    "ICN",
    "INP",
    "ISC",
    "N",
    "PGH",
    "PIE",
    "PL",
    "PLC",
    "PLE",
    "PLR",
    "PLW",
    # "PT", # flake8-pytest-style
    "PYI",
    "Q",
    "RUF",
    "RSE",
    "RET",
    "S",
    "SIM",
    "SLF",
    "T",
    "T10",
    "T20",
    "TCH",
    "TID",
    # "TRY", # tryceratops
    # "UP", # pyupgrade
    "W",
    "YTT",
]
extend-select = ["I"]
ignore = [
  "A001",  # Variable is shadowing a Python builtin
  "ANN101",  # Missing type annotation for self
  "ANN102",  # Missing type annotation for cls
  "ANN204",  # Missing return type annotation for special method __str__
  "ANN401",  # Dynamically typed expressions (typing.Any) are disallowed
  "ARG005",  # Unused lambda argument
  "C901",  # Too complex
  "D105",  # Missing docstring in magic method
  "D417",  # Missing argument description in the docstring
  "E501",  # Line too long
  "ERA001",  # Commented out code
  "G004",  # Logging statement uses f-string
  "PLR0911",  # Too many return statements
  "PLR0912",  # Too many branches
  "PLR0913",  # Too many arguments to function call
  "PLR0915",  # Too many statements
  "SLF001", # Private member accessed
  "TRY003",  # Avoid specifying long messages outside the exception class
]
fixable = [
    "F401", # Remove unused imports.
    "NPY001", # Fix numpy types, which are removed in 1.24.
]
unfixable = ["B"]
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".pytest_cache",
    ".vscode",
    "__pypackages__",
    "_build",
    "alembic",
    "buck-out",
    "node_modules",
    "venv",
    "site",
    "docs",
]
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.mccabe]
max-complexity = 10

[tool.ruff.isort]
lines-after-imports = 2
known-first-party = ["nendo"]

[tool.ruff.pydocstyle]
convention = "google"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
    """


@dataclasses.dataclass
class GenPluginInput:
    author_name: str
    plugin_name: str
    description: str
    plugin_type: str
    folder: str
    use_complex_docs: bool


def parse_input() -> GenPluginInput:
    plugin_types = {
        1: "NendoAnalysisPlugin",
        2: "NendoGeneratePlugin",
        3: "NendoEffectPlugin",
        4: "NendoLibraryPlugin",
    }

    console.clear()
    console.print("[bold #2dec92]Welcome to the nendo-core plugin generator. :wave:[/]")
    with Progress(
        TextColumn("", justify="right"),
        BarColumn(
            bar_width=None,
            style="#605DFF",
            complete_style="#2dec92",
            finished_style="#2dec92",
        ),
        console=console,
    ) as progress:

        def step():
            console.clear()
            progress.start()
            progress.update(task_id, advance=1)
            progress.stop()

        task_id = progress.add_task("", total=6)

        progress.stop()
        author_name = console.input("\n[bold #605DFF]Please enter your name:[/]\n")

        step()

        plugin_name = console.input(
            f"\n[bold #605DFF]Hi {author_name}! :grinning_face_with_smiling_eyes:\nPlease enter the name of the plugin you want to create:[/]\n"
        )

        step()

        description = console.input(
            f"\n[bold #605DFF]Great! :sign_of_the_horns:\nWhat is {plugin_name} about? Please enter a short description:[/]\n"
        )

        step()

        folder = console.input(
            f"\n[bold #605DFF]Sounds interesting! Can't wait to try it. :rocket:\nWhere do you want to create {plugin_name}? Please enter a path:[/]\n"
        )

        step()

        console.print(
            f"\n[bold #605DFF]Cool! What type of plugin is {plugin_name}?\nPlease enter one of {list(plugin_types.keys())}:[/]\n"
        )
        plugin_type = int(
            console.input(
                "\n".join(
                    [f"[bold #2dec92]{k}: {v}[/]" for k, v in plugin_types.items()]
                )
                + "\n"
            )
        )

        step()
        use_complex_docs = console.input(
            f"\n[bold #605DFF]One more thing! :index_pointing_up:\nDo you want to create complex docs using mkdocs? (otherwise I'll just create a README) (y/n) [/]\n"
        )

        step()

    return GenPluginInput(
        author_name=author_name,
        plugin_name=plugin_name,
        description=description,
        plugin_type=plugin_types[plugin_type],
        folder=folder,
        use_complex_docs=use_complex_docs == "y",
    )


def main():
    gen_plugin_input = parse_input()
    author_name = gen_plugin_input.author_name
    plugin_name = gen_plugin_input.plugin_name
    description = gen_plugin_input.description
    plugin_type = gen_plugin_input.plugin_type
    folder = gen_plugin_input.folder
    use_complex_docs = gen_plugin_input.use_complex_docs

    plugin_path = Path(folder) / plugin_name
    plugin_path.mkdir(parents=True, exist_ok=True)

    src_dir = plugin_path / "src" / plugin_name
    src_dir.mkdir(parents=True, exist_ok=True)

    test_dir = plugin_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)

    class_name = to_class_name(plugin_name)
    config_class_name = f"{class_name}Config"

    with open(plugin_path / "setup.py", "w") as f:
        f.write(create_setup_py(plugin_name, description, author_name))

    with open(plugin_path / "pyproject.toml", "w") as f:
        f.write(create_pyproject_toml(plugin_name, author_name, description))

    with open(plugin_path / "README.md", "w") as f:
        f.write(create_readme_md(plugin_name, description, author_name))

    if use_complex_docs:
        docs_dir = plugin_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        with open(docs_dir / "index.md", "w") as f:
            f.write('--8<-- "README.md"')

        with open(docs_dir / "example.md", "w") as f:
            f.write("# Example Page")

        with open(plugin_path / "mkdocs.yml", "w") as f:
            f.write(create_mkdocs_yml(plugin_name))

    with open(src_dir / "plugin.py", "w") as f:
        f.write(create_plugin_py(plugin_type, class_name, config_class_name))

    with open(src_dir / "config.py", "w") as f:
        f.write(create_config_py(config_class_name))

    with open(src_dir / "__init__.py", "w") as f:
        f.write(create_init_py(to_class_name(plugin_name)))

    with open(test_dir / f"test_{plugin_name}.py", "w") as f:
        f.write(create_test_py(plugin_name, class_name))

    assets_dir = test_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile("tests/assets/test.mp3", assets_dir / "test.mp3")

    console.print()
    console.print(
        create_success_message(author_name, plugin_name, folder, plugin_path),
        style="#2dec92",
    )

    # TODO add test generation
    # print(f"pytest")


if __name__ == "__main__":
    main()
