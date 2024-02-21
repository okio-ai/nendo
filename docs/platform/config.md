# Configuration

!!! tip "Running on localhost"
    When running Nendo Platform only on your local machine, you don't need to change any configuration parameters. Nendo Platform will run just fine with the default settings.

You can configure Nendo Platform by setting various configuration parameters. From the shell in which you are starting Nendo Platform, set any of the following environment variables that will be picked up when you call any of the `make` commands.

!!! example "Example: Enable SSL"
    ```bash
    export USE_SSL=true
    ```


**Environment Variable** | **Type** | **Default** | **Description** |
|---|---|---|---|
USE_GPU | `bool` | `true` | Flag that switches between GPU enabled and CPU-only mode. |
SERVER_URL | `str` | `"http://localhost"` | URL under which the server will be made available online. |
USER_STORAGE_SIZE | `int` | `-1` | Storage limit for the user's library in kb. If set to -1, no storage limit will be applied. |
USE_SSL | `bool` | `false` | Flag to switch SSL on or off. Make sure to also set `SSL_CERTIFICATE_PATH` and `SSL_KEY_PATH` or copy your certificate/key combination to the `./conf/nginx/certs/` folder. |
SSL_CERTIFICATE_PATH | `str` | `"./conf/nginx/certs/nendo.crt"` | Path to the SSL certificate file (only relevant when `USE_SSL=true`). |
SSL_KEY_PATH | `str` | `"./conf/nginx/certs/nendo.key"` | Path to the SSL key file (only relevant when `USE_SSL=true`). |
MAILGUN_FROM_ADDRESS | `str` | `"postmaster@yourdomain.com"` | Sets the `FROM` for administrative emails (registration, verification, password reset, etc.) from the server. |
MAILGUN_API_KEY | `str` | `"REPLACE_KEY"` | Mail API key. |
