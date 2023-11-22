- Inherit from which `class`?
- Run which tests?
- What is the `storage_driver` and how does it work?


# Writing a `LibraryPlugin`

We'll go step by step through all the files you need to create and what they'll do.

Remember the directory structure from before:

```shell
├── README.md
├── pyproject.toml
├── setup.py
├── src
│   └── nendo_plugin_destroy
│       ├── __init__.py
│       ├── config.py
│       └── plugin.py
```

Let's look into the different files now.

## Files

### plugin.py

The most important thing in your plugin. Here is where all your magic happens.
Below, you'll find a simple implementation that just overrides a single library method.
We'll go through it step by step.

```python
from logging import Logger
from nendo import Nendo, NendoConfig, NendoLibraryPlugin, NendoStorageLocalFS, NendoTrack


class MongoDBLibrary(NendoLibraryPlugin):
    """A MongoDB implementation of the nendo library."""
    config: NendoConfig = None
    user: NendoUser = None
    db: Engine = None
    storage_driver: NendoStorage = None

    def __init__(
        self,
        db: Optional[Engine] = None,
        config: Optional[NendoConfig] = None,
        user_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or plugin_config
        if self.storage_driver is None:
            self.storage_driver = schema.NendoStorageLocalFS(
                library_path=self.config.library_path, user_id=self.config.user_id,
            )
        self._connect(db, user_id)
        self.storage_driver.init_storage_for_user(user_id=self.user.id)

    def _connect(
        self,
        db: Optional[Engine] = None,
        user_id: Optional[uuid.UUID] = None,
    ):
        """Open mongodb session."""
        engine_string = (
            "mongodb:///?"
            f"Server={plugin_config.mongodb_host}&"
            f"Port={plugin_config.mongodb_port}&"
            f"Database={plugin_config.mongodb_db}&"
            f"User={plugin_config.mongodb_user}&"
            f"Password={plugin_config.mongodb_password}"
        )
        self.db = db or create_engine(engine_string)
        Base.metadata.create_all(bind=self.db)
        self.user = self.default_user
        return None

    def play(self, track: schema.NendoTrack) -> None:
        """Preview an audio track on mac & linux.

        Args:
            track (NendoTrack): The track to play.
        """
        play_signal(track.signal, track.sr)

```

The basics are very simple: Make sure to extend `NendoLibraryPlugin`, and make sure that your plugin connects to the database upon initialization.

### config.py

```python
from nendo import NendoConfig


class DestructionConfig(NendoConfig):
    """Configuration defaults for the destroy plugin."""
    my_default_param: bool = False

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
```

This class extends the base `NendoConfig` and allows you to define some default and overridable parameters for your
plugin.
It behaves just like `NendoConfig`, read up more on basic `nendo` configuration [here](../usage/config.md).

### setup.py

```python
from distutils.core import setup

if __name__ == "__main__":
    setup(
        name="nendo-plugin-destruct",
        version="0.1.0",
        description="Nendo destroyer plugin",
        author="Aaron Abebe <aaron@okio.ai>",
    )
```

This is a standard `setup.py` file.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).
You just need to define some basics like the name of your plugin, a version number and a description.

### pyproject.toml

All nendo plugins use `pyproject.toml` to manage their dependencies.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).

## Finished plugin

That's it!

!!! success
    When you're finished go back to the plugin development [overview](plugindev.md#running-a-plugin)
    and learn how to test and publish your plugin.


