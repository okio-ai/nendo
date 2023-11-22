# Configuration

There are two primary ways in which nendo can be configured:

**Passing a `NendoConfig` upon nendo initialization**

Inside your python app:

```python
from nendo import Nendo, NendoConfig

nd = Nendo(
    config=NendoConfig(
        library_path="./my_library",
        log_level="debug",
        # more configuration variables ...
    )
)
```

**Using environment variables**

Inside the shell, before starting Python, execute for each desired configuration variable:

```bash
$ export LIBRARY_PATH=./my_library
$ export LOG_LEVEL=debug
# more configuration variables ...
```

## Configuration Reference

| **NendoConfig** | **Env var** | **Type** | **Default** | **Description** |
|---|---|---|---|---|
| log_level | LOG_LEVEL | `str` | `"info"` | The log level with which the nendo logger runs. |
| log_file_path | LOG_FILE_PATH | `str` | `""` | The path to where the nendo log should be saved. If none is given (empty string), print to `stdout` |
| plugins | PLUGINS | `List[str]` | `[]` | List of plugins package names to be loaded with Nendo. |
| library_plugin | LIBRARY_PLUGIN | `str` | `"default"` | The name of the nendo library plugin to use. As all nendo plugins, their name follows the pattern `nendo_plugin_library_[name]`, where `[name]` is an arbitrary name. If set to `"default"`, the default [DuckDB](https://duckdb.org/) implementation of the [NendoLibrary]
(library.md) will be used. |
| library_path | LIBRARY_PATH | `str` | `"nendo_library"` | The path to the directory to be used for storing the nendo Library files. |
| user_name | USER_NAME | `str` | `"nendo"` | The name of the nendo user to be used for the [NendoLibrary](library.md). Only relevant if deploying nendo together with an API server. |
| user_id | USER_ID | `str` | `"ffffffff-1111-2222-3333-1234567890ab"` | The user ID of the default user to be used for the [NendoLibrary](library.md). Only relevant if deploying nendo together with an API server. |
| auto_resample | AUTO_RESAMPLE | `bool` | `False` | Flag that determines whether tracks should be automatically resampled upon import. |
| default_sr | DEFAULT_SR | `int` | `44100` | The default sample rate to be used when auto-resampling tracks upon import. |
| copy_to_library | COPY_TO_LIBRARY | `bool` | `True` | Flag that determines whether an imported track's file should be copied into the nendo library. |
| auto_convert | AUTO_CONVERT | `bool` | `True` | Flag that determines whether an imported track's file should be converted to Nendo's standard file format (`.wav`). |
| skip_duplicate | SKIP_DUPLICATE | `bool` | `True` | Flag that determines whether a track that points to a file that already exists in the library can be important multiple times. If True, always the file that already exists in the library will be used instead. |
| max_threads | MAX_THREADS | `int` | `2` | Maximum number of threads to be used for multiprocessing tasks. |
| batch_size | BATCH_SIZE | `int` | `10` | Batch size to use for multiprocessing tasks. |
| stream_mode | STREAM_MODE | `bool` | `False` | Flag that enables `stream mode`: With stream mode, all functions that return multiple items, such as e.g. `nd.get_tracks()` return an `Iterator` instead of a `List`. |
| stream_chunk_size | STREAM_CHUNK_SIZE | `int` | `1` | Size of the chunks (in items) in which the `Interator`s will give back the results. Ignored if `stream_mode` is `False`.