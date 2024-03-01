# Troubleshooting

This page serves as a technical FAQ and troubleshooting guide.

## GPU support

Most of the libraries polymath uses come with native GPU support through cuda. Please follow the [tensorflow documentation](https://www.tensorflow.org/install/pip) for instructions on how to set up use with cuda. If you have followed these steps, tensorflow and torch will both automatically pick up the GPU and use it.

## I see a strange warning in the logs about `nendo_plugin_embed_clap` not being found

If you see the following warning in the logs:

```
[2024-02-22T19:37:19.256Z] nendo WARNING Plugin with name nendo_plugin_embed_clap has been configured for the NendoLibraryVectorExtension but is not loaded. Please make sure to install and enable the plugin to use the embedding features of the nendo library.
```

Do not panic. This warning appears because we currently do not use the CLAP embedding plugin inside `nendo-server` directly. Instead, we run the plugin inside the tools (which are started in their own docker containers) so everything is fine and the warning can be ignored.
