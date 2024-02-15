# Quickstart

Nendo Platform is best controlled using `make`. To get an overview of the available commands, just call it directly:

```bash
make
```

Starting Nendo Platform is as simple as calling:

```bash
make run
```

!!! warning "SSL"
    Calling this command without any further [configuration](config.md) will launch Nendo Platform without SSL enabled. In local environments, this is fine but it is strongly advised not to run Nendo Platform without SSL and expose it to the internet.

    To enable SSL, set the `USE_SSL` environment variable to `true` before calling the above command.

Now start your browser and navigate to <a href="http://localhost" target="_blank">http://localhost</a> to view the Nendo Platform.

!!! info "Login"
    The default username / password combo for the dev superuser are:
    
        Username: dev@okio.ai
        Password: ChangeMe

## CPU-only mode

If your machine does not have a GPU, you can run Nendo Platform in CPU-only mode:

```bash
make run-cpu
```

!!! warning "Limitations of running without GPU"
    Many of the AI capabilities of a Nendo Platform require a GPU to run properly or at all. Expect some tools to fail in CPU-only mode.

## Development mode

If you want to run Nendo Platform in [development mode](development.md), call instead:

```bash
make run-dev
```
