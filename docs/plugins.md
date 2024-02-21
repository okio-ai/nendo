# Plugins

Nendo’s plugin architecture consists of two types of architecture components: 
The core system and plug-in modules. 
Application logic is divided between independent plugin modules and the basic core system, 
reducing the number of dependencies and providing extensibility, flexibility, and isolation of application features.

## Installing a plugin

To install a plugin, simply install the corresponding package with your favorite package manager, e.g. `pip`. 

```bash
pip install nendo-plugin-example
```

## Enabling a plugin

To configure nendo to load an installed plugin upon startup, add its name to the list of activated plugins given by `NendoConfig.plugins`.

!!! example
    ```python
    from nendo import Nendo, NendoConfig
    nd = Nendo(
        config=NendoConfig(
            plugins=["nendo_plugin_example"]
        )
    )
    ```

## Running a plugin

There are multiple ways to run a plugin in nendo. 
The most general way is to call it directly from nendo's plugin registry, 
by accessing it without the `nendo_plugin_` prefix:

```pycon
>>> my_track = nd.add_track(file_path='/path/to/file.mp3')
>>> result = nd.plugins.example(track=my_track) # this runs the plugin
```

Alternatively, a plugin can be called directly on a track/collection via the `process` method:

!!! tip 
    This also allows you to easily chain plugins!

    ```pycon
    >>> my_track = nd.add_track(path='/path/to/file.mp3')
    >>> result = track.process('nendo_plugin_example') # this runs the plugin
    >>> chained_result = track.process('nendo_plugin_example').process('nendo_plugin_example_2') # this chains two plugins
    ```

## Plugin Types

The following is a comprehensive list of all plugin types available in Nendo Core. 
For information on how to implement your own plugins of each type, refer to the [developer pages](development/plugindev.md) of the documentation.

=== "Analysis Plugin"

    Analysis plugins are used to extract and save any kind of information from a `NendoTrack` or `NendoCollection`, 
    e.g. key, bpm, beat positions, but also things like textual transcriptions, or any other kind of metadata.

=== "Generate Plugin"

    Generate plugins are used to generate new content from a `NendoTrack` or `NendoCollection`, 
    but also just using a prompt or a seed or any kind of input information.

=== "Effect Plugin"

    Effect plugins are used to apply effects to a `NendoTrack` or `NendoCollection`.

=== "Library Plugin"

    Library plugins are used to modify the `NendoLibrary` itself, e.g. change the way data is saved, 
    allow different integrations with other data management methods or services.

=== "Embedding Plugin"

    Embedding plugins are used to compute vector embeddings from `NendoTrack` and `NendoCollection` objects. They may use the track's waveform, a text representation of it's metadata, or both.

=== "Utility Plugin"

    Utility plugins are simple plugins that take and input, for example a piece of text, and transform it. A typical example of such a plugin would be a Large Language Model that is used to summarize the transcription of a song's lyrics.
