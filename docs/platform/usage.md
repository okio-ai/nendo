# Quickstart

Nenod Platform is best controlled using `make`. To get an overview of the available commands, just call it directly:

```bash
make
```

Starting Nendo Platform is as simple as calling:

```bash
make run
```

!!! warning "SSL"
    Calling this command without any further [configuration](config.md) will launch Nendo Platform without SSL enabled. In local environments, this is fine but it is strongly advised not to run Nendo Platform without SSL and expose it to the internet.

Now start your browser and navigate to <a href="http://localhost" target="_blank">http://localhost</a> to view the Nendo Platform.

!!! info "Login"
    The default username / password combo for the dev superuser are:
    
        Username: dev@okio.ai
        Password: ChangeMe

