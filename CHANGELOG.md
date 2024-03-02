# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.2.2](https://github.com/okio-ai/nendo/releases/tag/0.2.2) - 2024-03-02

<small>[Compare with 0.2.1](https://github.com/okio-ai/nendo/compare/0.2.1...0.2.2)</small>

### Bug Fixes

- set fallback track title without extension ([06396e6](https://github.com/okio-ai/nendo/commit/06396e66bc8360c462ea64e0350f9e3a4001ac89) by faradox).
- add sanitization of strings for json insert ([65b5cf5](https://github.com/okio-ai/nendo/commit/65b5cf5ec2685410d013b1616c070fd6a8747dd0) by faradox).

### Docs

- improve documentation in various places ([a084146](https://github.com/okio-ai/nendo/commit/a0841468a93e25cd0a8000d9883b057897861e0e) by faradox).

## [0.2.1](https://github.com/okio-ai/nendo/releases/tag/0.2.1) - 2024-02-28

<small>[Compare with 0.2.0](https://github.com/okio-ai/nendo/compare/0.2.0...0.2.1)</small>

### Bug Fixes

- add_tracks should return a list of tracks (#19) ([78ba963](https://github.com/okio-ai/nendo/commit/78ba963e35453409e6a02c53438d8fc433a96a02) by Aaron Abebe).
- skip_duplicate doesn't respect user_id ([741babc](https://github.com/okio-ai/nendo/commit/741babc905d3fe2096baaa21d2193625799ce50a) by Felix Lorenz).

## [0.2.0](https://github.com/okio-ai/nendo/releases/tag/0.2.0) - 2024-02-19

<small>[Compare with 0.1.3](https://github.com/okio-ai/nendo/compare/0.1.3...0.2.0)</small>

### Features

- Added the first extension for the Nendo Library: The `NendoLibraryVectorExtension` is a mix-in class that can be used by implementations of the Nendo Library to add support for saving and retrieving embedding vectors.
- Added a new class `NendoEmbedding` that represents an embedding of a `NendoTrack` and stores the vector together with the ID of the track from which it was computed, the text representation of the track that was used to compute the embedding, as well as the embedding plugin's name and version that were used to compute the embedding.
- Added a new subclass of the `NendoPlugin` called `EmbeddingPlugin` that accepts either a `NendoTrack`, a `NendoCollection`, a `signal` and a `text`, or only a `text` and computes corresponding `NendoEmbedding`(s), depending on whether a single object or a `NendoCollection` was provided. It also determines whether the currently used `NendoLibrary` implementation uses the `NendoLibraryVectorExtension` and, if so, saves the computed embeddings directly to the library.
- Added the global configuration variable `replace_plugin_data`, that specifies whether new plugin data will overwrite existing plugin data for the specific plugin name and version used to generate the data.
- Reworked the way relationships between tracks are managed. Previously, Nendo would create bidirectional relationships, which caused problems with the retrieval of related tracks, especially when using paging (i.e. `offset` and `limit`). The new approach is to only store relationships _from_ a derivative track _to_ the original track from which it was derived. Accordingly, all functions for retrieving related tracks accept a new parameter, `direction: str`, which can assume either one of the values `"to"`, `"from"` and `"both"` and will change their retrieval behavior accordingly. Also, the method names for some methods were changed to reflect the new semantics more accurrately: `NendoTrack.has_relationship_to()` was replaced by `NendoTrack.has_related_track(direction=...)`. `collection.has_relationship_to()` was replaced by `collection.has_related_collection()`.
- Added a new shortcut function `NendoTrack.relate_to_track()` that creates a relationship of the specified `relationship_type` and with the specified metadata from the given track _to_ another track.
- Two new shortcut functions `NendoTrack.refresh()` and `collection.refresh()` were added that retrieve the latest version of the given object as it exists in the Nendo Library, effectively allowing to quickly pull the latest changes to an object from the database.
- The `NendoTrack.get_plugin_data()` methods signature was extended to allow for filtering a track's plugin data also by `plugin_version` and `user_id` in addition to the existing filters.
- Adjusted the `add_track()` function:
    - Stores all the ID3 metadata in `NendoTrack.meta` instead of `NendoTrack.resource.meta`.
    - If no ID3 metadata was found `NendoTrack.meta.title` will be set to the original name of the imported file.
- Added the `load_related_tracks: bool = False` flag to the `NendoLibrary.get_tracks()` function that allows to enable/disable the populating of the `NendoTrack.related_tracks` field upon retrieval of many tracks from the Nendo Library. This optimizes the performance of the call and allows to retrieve smaller objects that are more suitable for network transmission in web applications that use Nendo Core.
-  Add support for `NendoLibrary.filter_tracks(collection_id="...", order_by="collection")` that allows to order of the retrieved tracks by their `relationship_position` in the referenced collection.
- Added the `NendoLibrary.filter_related_tracks()` method to allow for filtering of related tracks queries.
- Changed the `NendoLibrary.filter_tracks()` method to search over `NendoTrack.meta` in addition to `NendoTrack.resource`. Changed the name of the `resource_filters` argument to `search_meta` to reflect the new behavior.
- Added the `NendoLibrary.add_tracks_to_collection()` function to allow for multiple tracks given as a list of IDs to be added to the specified collection.
- Added the `order` parameter to the `NendoLibrary.get_collection_tracks()` function to allow for control of the ordering. Defaults to `"asc"`, which will order the collection's tracks in ascending order of their `relationship_position`.
- Changed the signature and behavior of the `get_collection()` function:
    - Renamed the `details` parameter to `get_related_tracks` to better reflect it's effect on the function. The parameter controls whether the `NendoCollection.related_tracks` field will be populated.
    - The function now always returns a `NendoCollection` instead of returning a `NendoCollectionSlim` if `details=False` as is was previously.
- Added the `user_id` parameter to the following functions:
    - `NendoTrack.local()`
    - `NendoTrack.get_plugin_value()`
    - `NendoLibrary.get_track()`
    - `NendoLibrary.remove_collection()`
- Changed the signature of the `NendoLibrary.add_plugin_data()` function to make specifying of the `plugin_version` optional. If none is given, version will be inferred from the currently registered version of the plugin.
- Extended the signature of the `NendoLibrary.filter_collections()` function by the `collection_types` parameter to also allow for filtering by a list of collection types.
- Added the `NendoLibrary.library_size()` and `NendoLirary.collection_size()` functions to get the number of tracks in the library per user and the number of tracks in a collection, respectively.

### Bug Fixes

- Fixed a problem with the way dictionaries (like `NendoTrack.meta` and `NendoTrack.resource`) were stored in the Nendo Library which resulted in them being stored as JSON strings instead of JSON dictionaries. **This means that upgrading Nendo will break any apps that use libraries that were created with previous versions of nendo.** Please make sure you understand the implications and either flush your DB or convert it to match the new data model.
- Fixed a bug where the length of a `NendoTrack` would not be correctly determined if the track had a mono signal.
- A bunch of small bugfixes, too many to mention them all here.

## [0.1.3](https://github.com/okio-ai/nendo/releases/tag/0.1.3) - 2023-12-08

<small>[Compare with 0.1.2](https://github.com/okio-ai/nendo/compare/0.1.2...0.1.3)</small>

### Bug Fixes

- remove psycopg2 dependency (#15) ([ebd4a23](https://github.com/okio-ai/nendo/commit/ebd4a234d8cad32fad832093ca9808a07ed2375c) by Felix Lorenz).

## [0.1.2](https://github.com/okio-ai/nendo/releases/tag/0.1.2) - 2023-11-30

<small>[Compare with previous version](https://github.com/okio-ai/nendo/compare/0.1.1...0.1.2)</small>

### Features

- Enable iterating over collections (#12) ([576cd7e](https://github.com/okio-ai/nendo/commit/576cd7e08d8c6dc682a89c4043d374f562446bce)).

### Bug Fixes

- Make `plugin_version` optional when adding plugin data (#13) ([d5c9b73](https://github.com/okio-ai/nendo/commit/d5c9b7359bc0aba0b1b9156b3365eda61ec06ab8)).
- Fix a bug in `add_tracks()`; fixed a bug in `remove_track()`; fixed tests (#9) ([0aebb72](https://github.com/okio-ai/nendo/commit/0aebb72cca60799a9ccb458e3c6689896e5bccad)).
- Change `get_plugin_data()` to always return a list; Add `get_plugin_value()` to get string values for specific `plugin_data` key (#11) ([3277910](https://github.com/okio-ai/nendo/commit/32779100c01d6306d435b632e2c62a80bbc436fc)).
- Fix a bug with with `filter_tracks()` argument `track_type` (#8) ([748a352](https://github.com/okio-ai/nendo/commit/748a352c213660cc36a017c73129a040dad97985)).

### Docs

- Remove "How to write documentation" page; Document the design decision relating to dependencies between nendo plugins (#10) ([c7b05d3](https://github.com/okio-ai/nendo/commit/c7b05d3ab41d64e4f123261877e7d1a0915c43d2)).
- Update discord link in readme ([0eb85ad](https://github.com/okio-ai/nendo/commit/0eb85ad3c8acd3ed2f4841474b98eb951483a68e)).
- Update requirements in README (#7) ([f71ce94](https://github.com/okio-ai/nendo/commit/f71ce94c0dd8f17775b3b787456e98bf17ec83f3)).

## [0.1.1](https://github.com/okio-ai/nendo/releases/tag/0.1.1) - 2023-11-24

<small>[Compare with previous version](https://github.com/okio-ai/nendo/compare/0.1.0...0.1.1)</small>

### Bug Fixes

- Fix the collection export in the sqlalchemy plugin (#4)

### Docs

- Small improvements to the documentation (#3)

## [0.1.0](https://github.com/okio-ai/nendo/releases/tag/0.1.0) - 2023-11-22

<small>[Compare with first commit](https://github.com/okio-ai/nendo/compare/5ae77e8d3cdf75802a395d91dbf31f4adf63d979...0.1.0)</small>
