# Writing an `AnalysisPlugin`

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
I took the liberty to implement a simple plugin that just adds some important metadata to a track.
We'll go through it step by step.

```python
from logging import Logger
from nendo import Nendo, NendoConfig, NendoAnalysisPlugin, NendoTrack


class DestructionAnalyzer(NendoAnalysisPlugin):
    """Find out how weird your music is."""
    nendo_instance: Nendo = None
    config: NendoConfig = None
    logger: Logger = None

    @NendoAnalysisPlugin.plugin_data
    def analyze_devo_ness(self, track: NendoTrack):
        """Q: Are we not men? A: We are Devo!"""
        return {"are_we_not_men": "we_are_devo"}

    @NendoAnalysisPlugin.plugin_data
    def analyze_destruction(self, track: NendoTrack):
        """Check if a track is destroyed: Answer is always YES!"""
        return {"destroyed": "yes"}

    @NendoAnalysisPlugin.run_track
    def is_fucked_up(self, track: NendoTrack, use_full_analysis: bool = True):
        if use_full_analysis:
            self.analyze_devo_ness(track)
        self.analyze_destruction(track)
```

The basics are very simple: Make sure to extend `NendoAnalysisPlugin`, and make sure that your extended class has at
least
one method that is decorated with `@NendoAnalysisPlugin.run_track` or `@NendoAnalysisPlugin.run_collection`.
If you used the official setup script, these steps are already taken care of.

Then your plugin can have a few different methods that do the concrete metadata extraction and addition to
the `NendoTrack`.
These need to be decorated with `@NendoAnalysisPlugin.plugin_data`.

#### NendoAnalysis.plugin_data

This decorator automatically adds all calculated metadata to the `NendoTrack`'s `List[PluginData]`.
To learn more about `NendoTrack` or `PluginData` check out the API reference.

### config.py

```python
from nendo import NendoConfig


class DestructionConfig(NendoConfig):
    """Configuration defaults for the destroy plugin."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    my_default_param: bool = False
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
Make sure to also enter the same version in `src/nendo_plugin_destroy/__init__.py`.

### pyproject.toml

All nendo plugins use `pyproject.toml` to manage their dependencies.
You can read up more on how to configure it [here](https://packaging.python.org/tutorials/packaging-projects/).

## Finished plugin

That's it!

!!! success
    When you're finished go back to the plugin development [overview](plugindev.md#running-a-plugin)
    and learn how to test and publish your plugin.


