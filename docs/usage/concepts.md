# Basic Concepts

This page dives deeper into the basic concepts of Nendo Core:

- [Resource](#resource)
- [Track](#track)
- [Collection](#collection)
- [Relationship](#relationship)
- [Plugin](#plugin)
- [Plugin Data](#plugindata)

## Resource

The `NendoResource` encapsulates a physical file that resides either on local or remote storage and structures all relevant information for storing it in the [nendo library](library.md).

**Fields**

| Field | Type | Description |
| --- | --- | ---------------------------------------------------------------------------------------- |
| `#!py3 id` | `uuid` | The unique ID of the resource. |
| `#!py3 resource_type` | `str` | Denotes what kind of an object is stored. Possible values are `audio`, `image`, `model` and `blob`. |
| `#!py3 src` | `str` | The full disk to the actual file. Can be a path on disk or a URL to a bucket storage, for example. |
| `#!py3 location` | `str` | The (physical) location of the file. Possible values are `original` (somewhere on disk), `local` (inside the nendo library path, which is configured as `#!py3 Nendo.config.library_path`), `gcs` and `s3`. |
| `#!py3 meta` | `dict` | A dictionary that can be used to store additional metadata related to the resource. |

??? info "Files with `#!py3 location = original`"
    Nendo _never_ changes anything about files that reside at their `original` location. Only `local` files can be changed, deleted, etc.

## Track

In Nendo Core, a track is represented by the `#!py3 class NendoTrack` and serves as the fundamental building block of your next-gen audio processing workflows. In simple terms, it

- contains at least one audio [resource](#resource),
- can have [relationships](#relationship) to other tracks and [collections](#collection),
- can be used as an input for a nendo [plugin](#plugin), and
- can have multiple [plugin data](#plugindata) objects atteched to it.

!!! tip "Refer to the [`NendoTrack` user guide](tracks.md) for more information."

## Collection

A collection is represented by the `#!py3 class NendoCollection` and, in summary, it

- must always have a `name`,
- can contain an arbitrary number of [tracks](#track) that are ordered inside the collection,
- can have [relationships](#relationship) to other collections, and
- can be processed by a nendo [plugins](#plugin).

!!! tip "Refer to the [`NendoCollection` user guide](collections.md) for more information."

## Relationship

The basic objects in Nendo Core can be related to each other by means of the `#!py3 class NendoRelationship`. Relationships allow to add additional structure to your audio library, by e.g. grouping tracks into collections, saving which track was generated based on which other track, from which track a collection of stems was derived, and so forth.

**Fields**

| Field | Type | Description |
| --- | --- | ---------------------------------------------------------------------------------------- |
| `#!py3 id` | `uuid` | The unique ID of the relationship. |
| `#!py3 source_id` | `uuid` | The unique ID of the source object of the relationship. |
| `#!py3 target_id` | `uuid` | The unique ID of the target object of the relationship.  |
| `#!py3 relationship_type` | `str` | A free-form type descriptor that can be used by developers to further differentiate between different kinds of collection objects. Unless explicitly set by the developer, `"relationship"` is used as a placeholder value.|
| `#!py3 meta` | `dict` | A dictionary that can be used to store additional metadata concerning the relationship. |

???+ info "Derived `NendoRelationship` types"
    While all relationships in Nendo Core inherit from the `NendoRelationship` base class, in practice most relationships you'll encounter will be either of `#!py3 class NendoTrackTrackRelationship`, `#!py3 class NendoTrackCollectionRelationship`, or of `#!py3 class NendoCollectionCollectionRelationship`, depending on the class of the `source` and `target` objects. The reason for this lies in relational DB implementations of the [nendo library](library.md), that must store the relationships in separate tables in order to know where to perform the lookup for the SQL `JOIN` operation. As a user, this should rarely matter and so is only mentioned as a side node here.

## Plugin

The plugin is a fundamental concept in Nendo Core and allows developers to flexibly extend nendo's capabilities. In summary, 

- plugins must be installed separately in addition to Nendo Core,
- must be enabled in the [nendo configuration](config.md) in order to be usable at runtime,
- can be run on both [tracks](#track) and [collections](#collection), and
- can be chained to realize complex audio processing pipelines.

!!! tip "Learn all albout how plugins work in the [plugin user guide](../plugins.md)."

## Plugin Data

Some [plugins](#plugin) in Nendo Core, upon being run on a [track](#track) or a [collection](#collection), produce objects of `#!py3 class NendoPluginData` that are saved to the [nendo library](library.md) and attached to the track for which they have been computed. This way, tracks can be enriched with all kinds of information that facilitates their further processing, filtering and recommendation.

!!! info "Accessing a track's plugin data"
    To learn more about how to read a track's plugin data, check the [`NendoTrack` user guide](tracks.md#producing-and-reading-plugin-data).

**Fields**

| Field | Type | Description |
| --- | --- | ---------------------------------------------------------------------------------------- |
| `#!py3 id` | `uuid` | The unique ID of the plugin data. |
| `#!py3 track_id` | `uuid` | The ID of the track to which the plugin data belongs. |
| `#!py3 plugin_name` | `str` | The name of the plugin that created the plugin data object. |
| `#!py3 plugin_version` | `str` | The version of the plugin that created the plugin data object. |
| `#!py3 key` | `str` | The key of the plugin data object. |
| `#!py3 value` | `str` | The value of the plugin data object. |

---

!!! success "That's all!"
    Now you should have a solid birds-eye view on all the important basic concepts in Nendo Core. In theory, you could start working with nendo right away but to get a better understanding of all of Nendo Core's powerful features, we recommend you to check out the in-depth guides on the concepts introduced above:
    
    - [:octicons-arrow-right-24: Tracks](tracks.md)
    - [:octicons-arrow-right-24: Collections](collections.md)
    - [:octicons-arrow-right-24: Library](library.md)
    - [:octicons-arrow-right-24: Plugins](../plugins.md)