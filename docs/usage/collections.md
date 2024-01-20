# The Nendo Collection

Together with the [NendoTrack](tracks.md), the `#!py3 class NendoCollection` is an instrumental object in Nendo Core. In essence, it's an ordered list of `NendoTrack` objects and provides various functions that make it easy to work with large numbers of audio artifacts at once and to group them logically. For example, a `NendoCollection` could be an album, a playlist, a set of stems obtained from a specific track, a dataset used to train a model, and so on.

???+ info "Developer info"
    If you are a developer, you might as well just directly dive into the [API Referece](https://okio.ai/docs/reference/). This page looks at the basic concepts from a _user's_ perspective.

**Fields**

| Field | Type | Description |
| --- | --- | ---------------------------------------------------------------------------------------- |
| `#!py3 id` | `uuid` | The unique ID of the collection. |
| `#!py3 uder_id` | `uuid` | The ID of the user who "owns" the collection. |
| `#!py3 name` | `str` | The name of the collection |
| `#!py3 description` | `str` | A description of the collection |
| `#!py3 collection_type` | `str` | A free-form type descriptor that can be used by developers to further differentiate between different kinds of collection objects. Unless explicitly set by the developer, `"collection"` is used as a placeholder value. |
| `#!py3 visibility` | `Visibility` | A special field that can be used by developers to assign different visibilities to collections that can be used to isolate collections between users. Possible values are `public`, `private` and `deleted`. |
| `#!py3 meta` | `dict` | A dictionary that can be used to store additional metadata related to the collection. |

!!! danger "Manually changing fields"
    It is not recommended to overwrite the fields mentioned in the above table manually! Instead, you should be using the functions described in the following paragraphs. If you end up manipulating the fields directly, be aware that things might break and that you need to manually persist any changes by [saving the track](#saving-exporting-and-deleting-a-track).

**Adding, accessing and removing tracks**

=== "Adding a track"

    !!! example

        ```python
        # collection = ...
        # track = ...
        collection.add_track(track.id)
        ```

=== "Getting all tracks"

    To get a list of all tracks contained in a given collection, use the `collection.tracks()` shorthand:

    !!! example

        ```python
        # collection = ...
        all_collection_tracks = collection.tracks()
        # all_collection_tracks is now a list of NendoTracks
        ```

    !!! info "Collection size"

        To count the number of tracks in a given collection, you can simply use `len(collection)`.

=== "Removing a track"

    !!! example

        ```python
        # collection = ...
        # track = ...
        collection.remove_track(track.id)
        ```

**Saving, exporting and deleting a collection**

When you change a collection by writing to any of its fields directly or delete the in-memory object by using python's `#!py3 del collection`, the changes are not persisted to the nendo library. You have to call the corresponding collection functions to persist your changes:

=== "Saving a collection"

    !!! example

        ```python
        # collection = ...
        collection.save()
        ```

=== "Exporting a collection"

    A collection can be exported to directory in a given format using the `NendoCollection.export()` function. The filenames will be automatically generated based on the track's `original_filename`, the `filename_suffix` (which is a function parameter) and the desired `file_format`.

    !!! example

        ```python
        # collection = ...
        collection.export(
            export_path="/path/to/export/to/",
            filename_suffix="my_collection",
            file_format="wav",
        )
        # the resulting filenames will follow the pattern
        # "/path/to/export/to/{original_filename}_my_collection_{timestamp}.wav"
        ```

    !!! tip "Supported formats"

        When exporting a track this way, the supported formats are `wav`, `mp3` and `ogg`.

=== "Deleting a collection"

    !!! example

        ```python
        # collection = ...
        collection.delete()
        # Now, the collection has been removed from the nendo library.
        # To also delete the object from memory, call:
        del collection
        ```

**Working with relationships**

As stated above, it is possible for collections in Nendo Core to have relationships to other collections, as well as to tracks. The following functions can be used to add and check for relationships between collections.

=== "Add related collection"

    To add a new collection to nendo that has a relationship to an existing given collection:

    !!! example

        ```python
        # collection_1 = ...
        # track_1 = ...
        collection_2 = collection_1.add_related_collection(
            track_ids=[track_1.id],
            name="related collection",
            description="collection with a relationship to another collection",
        )
        ```

=== "Check relationships"

    To check whether a `NendoCollection` has _any_ relationships, you can use:

    !!! example

        ```pycon
        >>> # collection = ...
        >>> collection.has_relationship()
        True
        ```

    And to check only for a specific `relationship_type`:

    !!! example

        ```pycon
        >>> # collection = ...
        >>> track.has_relationship(relationship_type="stem")
        False
        ```

=== "Check relationships to"

    To check whether a given collection has a relationship to another given collection:

    !!! example

        ```pycon
        >>> # collection_1 = ...
        >>> # collection_2 = collection_1.add_related_collection(...)
        >>> collection_1.has_related_collection(collection_2.id)
        True
        ```

=== "Get all related collections"

    The `NendoCollection.related_collections` field contains a list of `NendoRelationship` objects. To obtain a list of all `NendoCollection` objects that are connected to the current collection by means of a `NendoRelationship`, you can use the `NendoCollection.get_related_collections()` method.

    !!! example

        ```python
        # collection = ...
        related_collections = collection.get_related_collections()
        ```

        Please refer to the [API reference](https://okio.ai/docs/reference/schema/core/#nendo.schema.core.NendoCollection.get_related_collections) to see the full list of parameters for this function.

**Running a plugin on a collection**

To run a plugin on a given `NendoCollection`, you can use the `#!py3 NendoCollection.process()` function. The following example will run the `classify_core` plugin on all tracks in the given collection:

!!! example

    ```python
    # collection = ...
    collection.process("classify_core")
    ```

### Working with a collection's metadata

Collections in nendo have metadata attached to them, in the form of the `NendoCollection.meta` dictionary. For example, upon importing track into the nendo library from a file, its parsed ID3 information is stored to `NendoCollection.meta`.

!!! note
    The `NendoCollection.meta` field is a normal dictionary, whose fields can be accessed simply via `collection.meta['source']` and added via `collection.meta.update({"source": "internet"})`. However, manipulating the `meta` dictionary directly like that will not persist the changes to the nendo library, which is why the functions below exist and should be used: They will take care of persisting any changes to the `meta` dictionary into the nendo library. 

=== "Adding metadata"

    Arbitrary metadata can be added to `NendoCollection.meta` by passing a dictionary with the desired `key: value` pairs:

    !!! example

        ```python
        # collection = ...
        collection.set_meta({"source": "internet"})
        ```

=== "Retrieving metadata"

    The `NendoCollection.meta` field is a normal dictionary, whose fields can be accessed simply via `collection.meta['source']`. However, there is also a convenience function that will return `None` if the key can not be found (instead of raising a `KeyError`):

    !!! example

        ```pycon
        >>> # collection = ...
        >>> existing_meta_value = collection.get_meta("source")
        >>> print(existing_meta_value)
        'internet'
        >>> missing_meta_value = collection.get_meta("something")
        >>> print(missing_meta_value)
        >>>
        ```

=== "Checking metadata"

    To check whether a given collection has metadata belonging to a specific key:

    !!! example
    
        ```pycon
        >>> # collection = ...
        >>> collection.has_meta("source")
        True
        >>> collection.has_meta("something")
        False
        ```

=== "Removing metadata"

    To remove a specific field from a collection's metadata:

    !!! example
        
        ```python
        # collection = ...
        collection.remove_meta("album")
        ```

---

!!! success
    That's all you need to know about the `NendoCollection`. Next up, get familiar with the [nendo library](library.md).