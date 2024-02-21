# First Steps with Nendo

Nendo makes it easy to create AI audio workflows and applications in just a few lines of code. This page aims to warm you up for the journey.

## Starting Nendo

To start Nendo with the default configuration, run the following inside the python environment of your choice (script, shell, notebook, etc.): 

```python
import nendo
nd = nendo.Nendo()
```

This will create a new instance of Nendo, using the default [library plugin](library.md) and the default library path `./nendo_library`, where the [database file](https://duckdb.org/docs/connect) and the audio files.

!!! tip 
    Check out the [configuration guide](config.md) to learn how to configure Nendo Core according to your needs.

## Add Your First Track

The fundamental object in Nendo Core is the `#!python class NendoTrack`. You can create one by loading an audio file from your harddisk:

```pycon
>>> my_track = nd.add_track("/path/to/file.wav")
>>> type(my_track)
<class 'nendo.schema.core.NendoTrack'>
>>> print(my_track)
... # pretty-printed track info
```

This will import the specified file into the [nendo library](library.md). To learn more about the `NendoTrack`, refer to the [collection user docs](tracks.md).

??? info "Supported audio codecs"
    Nendo supports a variety of audio codecs off the shelf. Supported filetypes are `.wav`, `.mp3`, `.ogg`, `.flac`, and `.aiff`.

## Create Your First Collection

Multiple `NendoTrack` objects can be grouped by means of a `#!python class NendoCollection`. For example, let's create a collection that contains only the track created above:

```pycon
>>> my_collection = nd.add_collection(
... name = "Collection 1",
... description = "My first nendo collection.",
... track_ids = [my_track.id],
... )
>>> type(my_collection)
<class 'nendo.schema.core.NendoCollection'>
```

And just like that, you created our first `NendoCollection` of type "playlist". To learn more about the `NendoCollection`, refer to the [collection user docs](collections.md).

## Run your first plugin

After you have [loaded your first NendoTrack](#managing-audio-files), it's time to run your first [plugin](../plugins.md) on it. This is where things start to get really interesting. First, you have to install a plugin. Let's begin with a simple one, the core classification plugin:

```bash
pip install nendo_plugin_classify_core
```

Next, you have configure nendo to load the plugin upon [startup](#starting-nendo):

```pycon
>>> from nendo import Nendo, NendoConfig
>>> nd = Nendo(config = NendoConfig(plugins=["nendo_plugin_classify_core"], log_level="info"))
[2023-11-18T09:45:28.555Z] nendo         INFO 1 registered plugins:
[2023-11-18T09:45:28.555Z] nendo         INFO classify_core - classify_core (0.1.0)
```

Finally, you can run the plugin on the track you created above:

```pycon
>>> nd.plugins.classify_core(my_track)
```

!!! tip
    You can run plugins on tracks _and_ on collections. Please refer to the [plugin section](../plugins.md) of this documentation for more information.

The core classification plugin will analyse the track and store the results in the library. To check the results of the analysis from the console, type:

```pycon
>>> for d in my_track.plugin_data:
...     print(d)
----------------
plugin name: nendo_plugin_classify_core
plugin version: 0.1.0
key: loudness
value: 105.32542419433594
```

!!! success
    That's it, you successfully completed your first steps with Nendo Core. :fontawesome-regular-face-smile-beam:

To dive deeper into Nendo Core, take a look at the following pages:

- [:octicons-arrow-right-24: Overview of basic concepts](concepts.md)
- [:octicons-arrow-right-24: Configuring Nendo Core](config.md)
- [:octicons-arrow-right-24: Learn about Tracks](tracks.md)
- [:octicons-arrow-right-24: Learn about Collections](collections.md)
- [:octicons-arrow-right-24: Learn about the Library](library.md)
- [:octicons-arrow-right-24: Learn about Plugins](../plugins.md)