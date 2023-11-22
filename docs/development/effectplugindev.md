# Writing a `EffectPlugin`

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
I took the liberty to implement a simple plugin that adds some "effects" a new track.
We'll go through it step by step.

```python
from logging import Logger
from typing import Tuple
import numpy as np
from nendo import Nendo, NendoConfig, NendoEffectPlugin


class DestructionGenerator(NendoEffectPlugin):
    """Generate some fucked up sounds."""
    nendo_instance: Nendo = None
    config: NendoConfig = None
    logger: Logger = None

    @NendoEffectPlugin.run_signal
    def generate_fuck_up(self, signal: np.ndarray, sr: int, destruction_factor: float = 0.2) -> Tuple[np.ndarray, int]:
        new_signal = signal * 100 * destruction_factor  # clip to death
        return new_signal, sr
```

If you used the plugin generation script you should already have most of this setup.

If not `(why????)` then the basics are very simple:
Make sure to extend `NendoEffectPlugin`, and make sure that your extended class has at least
one method that is decorated with `@NendoEffectPlugin.run_signal` `@NendoEffectPlugin.run_track`
or `@NendoEffectPlugin.run_collection`.

!!! note
For `NendoEffectPlugin`'s we recommend using `@run_signal`. Then nendo can handle everything else for you.


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

This class extends the base `NendoConfig` and allows you to define some default and overridable parameters for your plugin.
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


