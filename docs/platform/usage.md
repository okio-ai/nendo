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

    To enable SSL, refer to the [secure deployment](#server-deployment) below.

Now start your browser and navigate to <a href="http://localhost" target="_blank">http://localhost</a> to view the Nendo Platform.

!!! info "Login"
    The default username / password combo for the dev superuser are:
    
        Username: dev@okio.ai
        Password: ChangeMe
    
## Secure deployment

When deploying Nendo Platform to an internet-facing server, it is strongly recommended to set a few configuration variables to enable SSL before starting the server. 

To enable SSL, you need to configure the correct location of your SSL certificate and private key:

```bash
export SSL_CERTIFICATE_PATH=/path/to/my/certificate.crt
export SSL_KEY_PATH=/path/to/my/key.key
```

Alternatively, you can create the local directory `./cert` and add your certificate and key as `./conf/nginx/certs/nendo.crt` and `./conf/nginx/certs/nendo.key` and it will be picked up without the need to specify the above environment variables.

Next, set the `USE_SSL` variable to `true`:

```bash
export USE_SSL=true
```

Set the DNS name or IP address on which your server is listening:

```bash
# if your server has a domain name:
export SERVER_URL=https://my-nendo-server.com
# OR, if your server has only an IP address:
export SERVER_URL=https://192.168.0.1
```

Finally, change the password of the default user:

```bash
make set-password NEW_PASSWORD=mynewpassword
```

When everything is configured according to your setup, simply use `make run` again to start the stack, open your browser and navigate to your domain / IP address to start using Nendo Platform.

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

!!! danger
    Development mode is unsecure and should only be used in local environments.

