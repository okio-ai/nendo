# Writing an `EmbeddingPlugin`

We'll go step by step through all the files you need to create and what they'll do.

Remember the directory structure from before:

```shell
├── README.md
├── pyproject.toml
├── setup.py
├── src
│   └── nendo_plugin_embed_text
│       ├── __init__.py
│       ├── config.py
│       └── plugin.py
```

Let's look into the different files now.

## Files

### plugin.py

The most important file in your plugin. It is where the main plugin call code resides Let's go through it step by step.

```python
from logging import Logger
from my_embedding_model import MyModel
from nendo import Nendo, NendoConfig, NendoEmbeddingPlugin, NendoTrack
import numpy.typing as npt

from .config import EmbedTextConfig

settings = EmbedTextConfig()

class TextEmbedder(NendoEmbeddingPlugin):
    """Find out how weird your music is."""
    nendo_instance: Nendo = None
    config: NendoConfig = None
    logger: Logger = None
    model: MyModel = None
    device: str = None

    def __init__(self, **data: Any):
        """Initialize the plugin."""
        super().__init__(**data)
        self.model = MyModel.from_pretrained(settings.model).to(self.device)

    def track_to_text(self, track: NendoTrack) -> str:
        """Convert track to text."""
        text = ""
        for pd in track.get_plugin_data():
            text += f"{pd.key}: {pd.value}; "
        return text

    @NendoEmbeddingPlugin.run_track
    def embed_track(
        self,
        track: NendoTrack,
    ) -> Tuple[str, npt.NDArray]:
        text_representation = self.track_to_text(track)
        return (
            text_representation,
            self.model.embed_text(text_representation)
        )
```

The basics are very simple: Extend `NendoEmbeddingPlugin`, and make sure that your class has at least one method that is decorated with `@NendoEmbeddingPlugin.run_track`, `@NendoEmbeddingPlugin.run_collection`, `@NendoEmbeddingPlugin.run_signal_and_text` or `@NendoEmbeddingPlugin.run_text`.

#### NendoEmbeddingPlugin.run_track

The function receives the argument `track: NendoTrack` and returns a `Tuple` containing the embedded text as a string and the embedding as a `numpy.types.NDArray`.

#### NendoEmbeddingPlugin.run_collection

The function receives the argument `collection: NendoCollection` and returns a `Tuple` containing the embedded text as a string and the embedding as a `numpy.types.NDArray`.

#### NendoEmbeddingPlugin.run_signal_and_text

The function receives the arguments `signal: str` and `text: str` and returns a `Tuple` containing the embedded text as a string and the embedding as a `numpy.types.NDArray`.

#### NendoEmbeddingPlugin.run_text

The function receives the argument `text: str` and returns a `Tuple` containing the embedded text as a string and the embedding as a `numpy.types.NDArray`.

### config.py

```python
from nendo import NendoConfig


class EmbeddingTextConfig(NendoConfig):
    """Configuration defaults for the text embedding plugin."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    my_default_param: bool = False
```

This class extends the base `NendoConfig` and allows you to define some default and overridable parameters for your plugin.
It behaves just like `NendoConfig`, read up more on basic `nendo` configuration [here](../usage/config.md).

### setup.py

```python
from distutils.core import setup

if __name__ == "__main__":
    setup(
        name="nendo-plugin-embed-text",
        version="0.1.0",
        description="Nendo text embedding plugin",
        author="Author Name <author@email.com>",
    )
```

This is a standard `setup.py` file. You can read up more on how to configure it [in the python packaging docs](https://packaging.python.org/tutorials/packaging-projects/). You just need to define some basics like the name of your plugin, a version number and a description.
Make sure to specify the same version in `src/nendo_plugin_embed_text/__init__.py` and in `pyproject.toml`.

### pyproject.toml

All nendo plugins use `pyproject.toml` to manage their dependencies.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).

## Finished plugin

That's it!

!!! success
    When you're finished go back to the plugin development [overview](plugindev.md#running-a-plugin) and learn how to test and publish your plugin.
