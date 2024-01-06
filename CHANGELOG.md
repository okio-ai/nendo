# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
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
