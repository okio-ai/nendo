# Writing a `LibraryPlugin`

Writing a `LibraryPlugin` differs significantly from implementing any of the other plugin types. It requires the implementation of all functions defined by the `NendoLibraryPlugin`, which can be found in the [API Reference](https://okio.ai/docs/reference/schema/plugin/#nendo.schema.plugin.NendoLibraryPlugin). The following is a preliminary introduction and will be heavily extended in the future.

The plugin's directory structure is exactly the same as with any other kind of plugin:

```shell
├── README.md
├── pyproject.toml
├── setup.py
├── src
│   └── nendo_plugin_library_mongodb
│       ├── __init__.py
│       ├── config.py
│       └── plugin.py
```

## Files

### plugin.py

Below, you'll find a simple implementation that just implements the library initialization method and the `play()` method.

- To implement a new library plugin, you have two options:

    1. Inherit from the `SqlAlchemyNendoLibrary`, if your taget DBMS is compatible with SQLAlchemy, i.e. an SQLAlchemy driver exists for it. In this case, you only have to implement the initialization of the library as shown bove.
    1. Inherit from the `NendoLibraryPlugin`, and implement a general library plugin that does not use SQLAlchemy to connect to the DBMS backend. In this case, you have to implement/override all public methods defined in the `NendoLibraryPlugin`. Refer to the [API Reference](https://okio.ai/docs/reference/schema/plugin/#nendo.schema.plugin.NendoLibraryPlugin) to see the full list of functions that have to be implemented.

Below, we show how to implement a nendo library that uses the first approach, inheriting from the `SqlAlchemyNendoLibrary` plugin and implementing a `MongoDB` backend.

```python
from logging import Logger
from nendo import (
    NendoConfig,
    NendoStorage,
    NendoStorageLocalFS,
    NendoUser,
    SqlAlchemyNendoLibrary,
)
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import declarative_base

from .config import MongoDBConfig

plugin_package = metadata.metadata(__package__ or __name__)
plugin_config = MongoDBConfig()
Base = declarative_base(metadata=MetaData())
logger = logging.getLogger("nendo")


class MongoDBLibrary(SqlAlchemyNendoLibrary):
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
```

The basics are very simple:

- Use nendo's `NendoStorageLocalFS` storage driver or implement your own. Refer to the [API reference](https://okio.ai/docs/reference/schema/core/#nendo.schema.core.NendoStorage) to see which methods you need to implement for a `StorageDriver` to work.
- Overwrite any methods whose behavior you want to change but make sure that your implementation of the nendo library passes the library tests defined in `tests/test_library.py`.

### config.py

```python
from nendo import NendoConfig


class MongoDBConfig(NendoConfig):
    """Configuration defaults for the mongodb library plugin."""
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
        name="nendo-plugin-library-mongodb",
        version="0.1.0",
        description="Nendo mongodb library plugin",
        author="Felix Lorenz <felix@okio.ai>",
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
    When you're finished go back to the plugin development [overview](plugindev.md#publishing-a-plugin)
    and learn how to test and publish your plugin.
