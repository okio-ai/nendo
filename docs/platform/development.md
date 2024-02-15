# Development

Nendo Platform comes with a convenient _development mode_, in which the [nendo_web](web.md) and [nendo_server](server.md) components are updated upon any changes made to the codebase.

Use the following script to prepare the development environment for you:

```bash
make setup
```

!!! info ""
    This command has to be executed only once.

Then, whenever you want to start the development environment, run:

```bash
make run-dev
```

This will run Nendo Platform in development mode with more verbose logging and hot-reloading of components upon code changes.

!!! tip "Hot-reloading"
    The hot-reloading only works with changes that are done to the application code, i.e. code that resides in the `nendo_server/` subdirectory of `nendo_server` and in the `src/` subdirectory of `nendo_web` accordingly. All changes to files outside those directories require [rebuilding of the images, as explained below](#building).

Now you can start developing your app by changing files in the `repo/nendo_server` and `repo/nendo_web` directories.

## Building

If you end up changing something about `nendo_server` or `nendo_web` that requires (re-)building of the images, you should use the respective `make` commands for that. To build both images (server _and_ web):

```bash
# build for production
make build
# OR build for development
make build-dev
```

To only build `nendo_server`:

```bash
# build for production
make server-build
# OR build for development
make server-build-dev
```

To only build `nendo_web`:

```bash
# build for production
make web-build
# OR build for development
make web-build-dev
```

## Updating

To get the latest version of all involved repos and packages, use:

```bash
make update-dependencies
```

## Resetting

To completely erase the database and all associated audio files in the library, make sure the Nendo Platform is running and then call:

```bash
make flush
```

!!! danger "Danger"
    This will erase all data in your database and all audio files in the `library/` folder. Make sure you understand the consequences before executing this command.

## Debugging

To read the logs:

!!! example "Reading logs"

    ```bash
    # get the logs of nendo_server
    make server-logs
    # get the logs of nendo_web
    make web-logs
    ```

To get a shell into a running container:

!!! example "Getting shell access"

    ```bash
    # get a shell into nendo_server
    make server-shell
    # get a shell into nendo_web
    make web-shell
    ```
