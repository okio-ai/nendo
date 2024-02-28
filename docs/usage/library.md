# The Nendo Library

The nendo library is at the center of Nendo Core. It provides all functionalities required to handle a large catalog of audio assets, manage their metadata and group them logically into collections. Most library features can be accessed via shortcut functions, as explained in the [`NendoTrack`](tracks.md) and [`NendoCollection`](collections.md) user guides. In the following, we therefore focus on explaining the high-level ideas and providing some useful introductory examples.

!!! tip "For a list of all nendo library functions, refer to the [API reference](https://okio.ai/docs/reference/schema/plugin/#nendo.schema.plugin.NendoLibraryPlugin)"

## Configuring the Library Plugin

If left untouched, the default configuration of Nendo Core will use the `default` nendo library plugin, which is a [DuckDB](https://duckdb.org/) implementation of the nendo library.

!!! note "Using a different library plugin"
    You can change the library plugin to be used by nendo via the `nendo.config.library_plugin` configuration variable. For example, to use the [postgres implementation](https://okio.ai/docs/library-postgres/) of the nendo library plugin, set `nendo.config.library_plugin = nendo_plugin_library_postgres`.

The default implementation of the nendo library uses a local directory for storing its binary assets. You can control where the assets (such as audio files, blobs, etc.) should be stored via the `nendo.config.library_path` variable.

!!! note "The default library path is `./nendo_library`"

Furthermore, there are a number of other configuration variables that adjust how the nendo library behaves. Specifically, the variables `copy_to_library`, `skip_duplicate`, `auto_convert`, `auto_resample`, and `default_sr` are revelant, whose documentation can be found in the [configuration guide](config.md).

## Using the Library Plugin

The following paragraphs introduce the most essential functions to use when interacting with the nendo library.

??? warning "Preparations"
    The following examples assume that you have already created a nendo instance, e.g. with the default configuration:

    ```python
    nendo = Nendo()
    ```

The nendo library is available via the field `Nendo.library`. To 

!!! tip "Library access shortcuts"

    To make your code simpler, nendo allows to call _any_ library function directly on the main instance, such that, for example, `nendo.library.add_track("file.mp3")` can also be written as ``nendo.add_track("file.mp3")`.

### Adding audio files

The first step in most AI audio workflows is to import existing assets for analysis, generation and model training. The nendo library provides a set of functions that help adding individual files, as well as adding entire folders

=== "Adding a file"

    !!! example "Simple import"

        ```pycon
        >>> new_track = nendo.library.add_track("/path/to/my/file.mp3")
        >>> type(new_track)
        <class 'nendo.schema.core.NendoTrack'>
        ```
    
    !!! example "Duplicate import"

        To add the same track (of type `"voice"`) twice to the library:

        ```pycon
        >>> new_track = nendo.library.add_track("/path/to/my/file.mp3")
        >>> duplicate_track = nendo.library.add_track(
        ... file_path = "/path/to/my/file.mp3",
        ... track_type = "voice",
        ... skip_duplicate = False,
        ... )
        >>> new_track == duplicate_track
        False
        ```

    !!! example "Adding without import"

        ```pycon
        >>> new_track = nendo.library.add_track(
        ... file_path = "/path/to/my/file.mp3",
        ... copy_to_library = False,
        ... )
        >>> print(new_track.resource.src)
        /path/to/my/file.mp3
        ```


=== "Adding a directory"

    The following example adds all files in the target directory to nendo. The result is a `NendoCollection` containing all files as `NendoTracks`.

    !!! example

        ```pycon
        >>> added_tracks = nendo.library.add_tracks("/path/to/my/files/")
        >>> type(added_tracks)
        <class 'list'>
        >>> len(new_collection)
        32
        >>> type(added_tracks[0])
        <class 'nendo.schema.core.NendoTrack'>
        ```

=== "Creating a collection"

    !!! example "Creating an empty collection"

        ```pycon
        >>> new_collection = nendo.library.add_collection(
        ... name = "Empty collection",
        ... description = "My first nendo collection",
        ... collection_type = "playlist",
        ... visibilty = "private",
        ... )
        >>> type(new_collection)
        <class 'nendo.schema.core.NendoCollection'>
        >>> len(new_collection)
        0
        ```

    !!! example "Creating an collection from existing tracks"

        ```pycon
        >>> # new_track = ...
        >>> new_collection = nendo.library.add_collection(
        ... name = "New collection",
        ... track_ids = [new_track.id]
        ... )
        >>> len(new_collection)
        1
        ```

!!! tip
    The behavior of the above functions is influenced by the `copy_to_library` and `skip_duplicate` [configuration](config.md) variables. Passing parameters with the same names to the functions as demonstrated will overwrite the configured behavior for the single function call.

### Retrieving tracks and collections

Obtaining individual tracks and collections as well as all items in the library is 

??? info "Streaming mode"
    The `nendo.config.stream_mode` [configuration](config.md) variable can be used to change the behavior / return type of all library functions that retrieve multiple items. If `stream_mode` is set to `False`, the functions will return lists, whereas setting `stream_mode` to `True` will make them return [Iterators](https://wiki.python.org/moin/Iterator).

=== "Retrieve single item"

    !!! example

        ```pycon
        >>> track = nendo.library.get_track("c48d0436-6fa0-4cf6-9ab2-c6b00fbe3f91")
        >>> collection = nendo.library.get_collection("c01e9559-ac1b-4a2a-a30d-f038933ef5c0")
        ```

=== "Retrieve multiple items"

    !!! example "Retrieve multiple items as list"

        ```pycon
        >>> tracks = nendo.library.get_tracks(
        ... order_by = "created_at",
        ... limit = 10,
        ... offset = 0,
        ... )
        >>> len(tracks)
        10
        ```

    !!! example "Retrieve all items as iterator"

        ```pycon
        >>> nendo.config.stream_mode = True
        >>> collections = nendo.library.get_collections()
        >>> type(collections)
        <class 'generator'>
        >>> for c in collections:
        ...     print(c.id)
        "a11909ae-575e-40e6-9b80-c722c7ec85d4"
        "49efed34-3584-451d-83a8-b7bb8093a4ca"
        # ...
        ```

### Finding and filtering

Managing a large collection of audio files can be tedious. Nendo core allows to search through tracks, filter for specific keywords or plugin data values and to return the results as ordered lists. With `stream_mode` even large numbers of tracks can be efficiently iterated over. By using a combination of advanced nendo [plugins](../plugins.md), handling even very large audio libraries becomes easy. 

=== "Finding tracks"

    To find a track by searching over text representations of it's `meta` and `resource` fields, use the `#!py3 Nendo.library.find_tracks()` method.

    !!! example

        ```
        found_tracks = nendo.library.find_tracks(value = "bounce")
        ```

    Note, that like all functions in the nendo library that retrieve multiple items at once, the `#!py3 find_tracks()` function accepts the additional parameters `user_id`, `order_by`, `order`, `limit` and `offset`, which can be useful for developers using nendo inside their (paginated) web applications.

    ??? warning "Performance of the default implementation"
        Unfortunately, due to the simplistic implementation of this function in the `default` nendo library, it will not be very efficient for very large databases. If you are running into performance issues, consider switching to a more advanced implementation of the nendo library like the [postgres library plugin](https://okio.ai/docs/library-postgres/) or using the `Nendo.library.filter_tracks()` function which leverages the `resource` field's structure to make the matching more efficient.

=== "Finding collections"

    To find a collection by searching over it's `name` and `decription` fields, use the `#!py3 Nendo.library.find_collections()` method.

    !!! example

        ```
        found_collections = nendo.library.find_collections(value = "greatest hits")
        ```

    Note, that like all functions in the nendo library that retrieve multiple items at once, the `#!py3 find_collections()` function accepts the additional parameters `user_id`, `order_by`, `order`, `limit` and `offset`, which can be useful for developers using nendo inside their (paginated) web applications.


=== "Filtering tracks"

    Filtering tracks with regard to specific fields is one of the most complex operations supported by the nendo library. The `#!py3 filter_tracks()` method comes with a number of parameters that can be used in isolation or in conjunction to refine the search. The following examples provides a simple introduction, followed by a comprehensive list of supported paramters and their filtering effects.

    !!! example "Filtering by track_type"

        The following call will filter all tracks whose `track_type` field has the value `"voice"`:

        ```python
        voice_tracks = nendo.library.filter_tracks(track_type = "voice")
        ```

    !!! example "Filtering by collection"

        The following call will filter all tracks whose `track_type` field has the value `"voice"` and who are contained in the collection with the ID `ba57d368-94a5-4ded-8b1c-478026e24a66`:

        ```python
        collection_tracks = nendo.library.filter_tracks(
            track_type = "voice",
            collection_id = "ba57d368-94a5-4ded-8b1c-478026e24a66",
        )
        ```

    !!! example "Filtering by search value"

        The following call will filter all tracks wehre both words `"Michael"` and `"Jackson"` occur anywhere in their `track.meta` or `track.resource.meta` fields:

        ```python
        mj_tracks = nendo.library.filter_tracks(
            search_meta = ["Michael", "Jackson"],
        )
        ```
    
    !!! example "Filtering by plugin data range"

        The following call will filter all tracks whose `plugin_data` have an entry created by the `nendo_plugin_classify_core` plugin where the `bpm` value is between 100 and 120:

        ```python
        bpm_filtered_tracks = nendo.library.filter_tracks(
            filters = {"bpm": (100, 120)},
            plugin_names = ["nendo_plugin_classify_core"],
        )
        ```

     The following table provides an overview over the parameters and how they affect the search.

    | Parameter | Type | Description |
    | --- | --- | ---------------------------------------------------------------------------------------- |
    | `#!py3 filters` | `dict` | Filters to apply to the `plugin_data` field of the track. The dictionary can contain multiple filters, where the key is matched against the `key` of the `NendoPluginData` entry and the value can be either of the following: <ul><li>`tuple` - Check, whether the plugin data's `value` is in the range specified by the `tuple`.</li><li>`list` - Check, whether the plugin data's `value` matches any of the items in the list.</li><li>`str` - Do a fuzzy match comparison between plugin data's `value` and the `value` passed in the `filters` dictionary.</li></ul> |
    | `#!py3 search_meta` | `dict` | Dictionary containing the keywords to search for over the track.resource.meta field. The dictionary's values should contain singular search tokens and the keys have no effect in the `default` implementation of the nendo library. |
    | `#!py3 track_type` | `str` | Match the `NendoTrack.track_type` field against this value. |
    | `#!py3 user_id` | `uuid` | Filter for tracks with the given `user_id`. |
    | `#!py3 collection_id` | `uuid` | Filter for tracks who have a relationship to the collection with the given ID. |
    | `#!py3 plugin_names` | `list[str]` | Filter to apply in addition to the fields above, when filtering with respect to `plugin_data` entries. |


### Library integrity functions

The nendo library also comes with a few functions that can be used to verify and restore it's integrity, in cases where files have been (re)moved from their original locations without updating the corresponding tracks in the nendo library.

=== "Resetting the library"

    To reset the nendo library, deleteing all data and corresponding files, simply call `#!py3 nendo.library.reset()`. Calling this function will prompt the user to confirm the operation, unless the function parameter `force = True` is passed.

    !!! danger "Resetting the library"

        Resetting the library will purge all items from the database and delete the corresponding files from their location in the `library_path`. Files residing outside the nendo library, who were added to the library with the configuration parameter `config_to_library = False`, will not be deleted.

=== "Verifying the library integrity"

    To verify every track in the nendo library with respect to the existence of it's associated `resource` on disk, call `#!py3 nendo.library.verify()`. For every inconsistency thus detected, the user will be prompted how to act, allowing to type the letter **"i"** to ignore the specific inconsistency _or_ the letter **"r"** to resolve the inconsistency, by

    - removing the physical file if no corresponding database entry exists, or
    - removing the database entry if no corresponding file exists.

### Working with binary data (blobs)

Pieces of binary data are called `blobs` in nendo. They can be stored, loaded and removed from the nendo library by using the corresponding library functions introduced below.

=== "Storing a blob"

    To store a binary file into the nendo library, use `#!py3 nendo.library.store_blob(file_path)`.

    Likewise, to store a `bytes` object from memory by [pickling](https://docs.python.org/3/library/pickle.html) it onto disk and storing a corresponding object in the nendo library, use `#!py3 nendo.library.store_blob_from_bytes(data)`.

    !!! example

        ```pycon
        >>> # to store a blob from a binary file:
        >>> file_blob = nendo.library.store_blob(file_path = "/path/to/blob")
        >>> # to store a blob from a bytes object:
        >>> bytes_obj = os.urandom(16) # get a random bytes object
        >>> bytes_blob = nendo.library.store_blob_from_bytes(data = bytes_obj)
        ```

=== "Loading a blob"

    To obtain a blob from the nendo library and load the corresponding binary file into memory, use `#!py3 nendo.library.load_blob()`.
    
    !!! example

        ```python
        # blob_id = ...
        blob = nendo.library.load_blob(blob_id)
        ```

=== "Removing a blob"

    To remove a blob from the nendo library, use `#!py3 nendo.library.remove_blob()`.

    !!! example

        ```python
        # blob_id = ...
        blob = nendo.library.remove_blob(blob_id)
        ```

## Writing a Library Plugin

Please refer to the [library plugin development pages](../development/libraryplugindev.md).

---

!!! success
    That's all you need to know about the nendo library. Next up, dive deeper into the concept of [plugins in nendo](../plugins.md).