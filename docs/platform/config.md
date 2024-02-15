# Configuration

!!! info "Running on localhost"
    When running Nendo Platform only on your local machine, you don't need to change any configuration parameters. Nendo Platform will run just fine with the default settings.

You can configure Nendo Platform by setting various configuration parameters. From the shell in which you are starting Nendo Platform, set any of the following environment variables that will be picked up when you call any of the `make` commands:

```bash
# Disable GPU:
export USE_GPU=false
# URL where the Nendo Platform will available:
export SERVER_URL=https://my-domain.com
# Disable SSL (make sure that your SERVER_URL starts with "http://" in this case):
export USE_SSL=false
# Set the path to the SSL certificate file
export SSL_CERTIFICATE_PATH=/path/to/my/cert.pem
# Set the path to the SSL key file
export SSL_KEY_PATH=/path/to/my/key.pem
# Set the "from" address used for emails sent via mailgun:
export MAILGUN_FROM_ADDRESS=noreply@my-domain.com
# Set the mailgun API key:
export MAILGUN_API_KEY=aaaa-bbbb-cccc
```
