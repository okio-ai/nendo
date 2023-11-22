# Writing a `GeneratePlugin`

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
I took the liberty to implement a simple plugin that generates a new track or extends an existing track
based on some crazy shit.
We'll go through it step by step.

```python
from logging import Logger
from typing import Optional

import numpy as np
from nendo import Nendo, NendoConfig, NendoGeneratePlugin, NendoTrack


class DestructionGenerator(NendoGeneratePlugin):
    """Generate some weird sounds."""
    nendo_instance: Nendo = None
    config: NendoConfig = None
    logger: Logger = None

    @NendoGeneratePlugin.run_signal
    def generate_fuck_up(self, track: Optional[NendoTrack] = None, destruction_factor: float = 0.2) -> NendoTrack:
        sr = 44100
        if track is None:
            # "generate" audio from scratch
            signal = np.random.rand(2, sr * 30) * destruction_factor
            return self.nendo_instance.library.add_track_from_signal(signal=signal, sr=sr)
        
        # do some "outpainting"
        new_signal = np.vstack((track.signal, np.random.rand(2, sr * 30)))
        return self.nendo_instance.library.add_related_track_from_signal(
            signal=new_signal,
            sr=sr,
            related_track_id=track.id
        )
```

If you used the plugin generation script you should already have most of this setup. 

If not `(why????)` then the basics are very simple: 
Make sure to extend `NendoGeneratePlugin`, and make sure that your extended class has at least
one method that is decorated with `@NendoGeneratePlugin.run_signal`, `@NendoGeneratePlugin.run_track` 
or `@NendoGeneratePlugin.run_collection`.

!!! note
    For `NendoGeneratePlugin`'s we recommend using `@run_track` 
    because you might want to save some metadata to the track as well.


### config.py
```python
from nendo import NendoConfig
class DestructionConfig(NendoConfig):
    """Configuration defaults for the destroy plugin."""
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
        name="nendo-plugin-destruct",
        version="0.1.0",
        description="Nendo destroyer plugin",
        author="Aaron Abebe <aaron@okio.ai>",
    )
```

This is a standard `setup.py` file.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).
You just need to define some basics like the name of your plugin, a version number and a description.
Make sure to also enter the same version in `src/nendo_plugin_destroy/__init__.py`.

### pyproject.toml

All nendo plugins use `pyproject.toml` to manage their dependencies.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).

## Finished plugin

That's it!

!!! success
    When you're finished go back to the plugin development [overview](plugindev.md#running-a-plugin)
    and learn how to test and publish your plugin.


