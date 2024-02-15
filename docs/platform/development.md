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

!!! note "Hot-reloading"
    The hot-reloading only works with changes that are done to the application code, i.e. code that resides in the `nendo_server/` subdirectory of `nendo_server` and in the `src/` subdirectory of `nendo_web` accordingly. All changes to files outside those directories require [rebuilding of the images, as explained below](#building).

Now you can start developing your app by changing files in the `repo/nendo_server` and `repo/nendo_web` directories.

## Building

If you end up changing something about `nendo_server` or `nendo_web` that requires (re-)building of the images, you should use the respective `make` commands for that. To build both images (server _and_ web):

```bash
make build
```

Alternatively, to build the development version of the images with hot-reloading upon changes to the codebase:

```bash
make build-dev
```

To only build `nendo_server`:

```bash
make server-build
# OR
make server-build-dev
```

To only build `nendo_web`:

```bash
make web-build
# OR
make web-build-dev
```

## Updating

To get the latest version of all involved repos and packages, use:

```bash
make update-dependencies
```

Then, in many cases, you need to rebuild the stack:

```bash
make build
# OR
make build-dev
```

## Resetting

To completely erase the database and all associated audio files in the library, make sure the Nendo Platform is running and then call:

```bash
make flush
```

**CAUTION: This will erase all data in your database and all audio files on the in the `library/` folder. Make sure you understand the consequences before executing this command.**

## Debugging

To get the logs of the `nendo_server` docker container:

```bash
make server-logs
```

To get the logs of the `nendo_web` docker container:

```bash
make web-logs
```

To get a shell into the running `nendo_server` container:

```bash
make server-shell
```

To get a shell into the running `nendo_web` container:

```bash
make web-shell
```
