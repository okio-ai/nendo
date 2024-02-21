# Nendo Platform

Nendo Platform is the feature-rich web application stack to develop and run new GUI-enabled tools that are based on Nendo Core and it's plugin ecosystem.

## Requirements

To run Nendo Platform, make sure you have `docker` and `docker-compose` (`>=1.28.0`) installed.

!!! info "Operating System Requirements"
    Currently, Linux is the only operating system that is officially supported by Nendo Platform. Feel free to try and run it on Mac OSX or Windows but expect certain Features to fail without significant modifications to its codebase.

!!! info "GPU Requirements"
    Nendo Platform needs a GPU with at least 24 GB of VRAM for all of its features to work properly. If your system does not have a GPU available, you can still run Nendo Platform in [CPU mode](platform/usage.md#cpu-only-mode) but expect certain tools to fail.

Visit the following pages to learn more about how to run and use Nendo Platform:

- [:octicons-arrow-right-24: Get Started](platform/usage.md)
- [:octicons-arrow-right-24: Configuration Guide](platform/config.md)
- [:octicons-arrow-right-24: Development Guide](platform/development.md)
- [:octicons-arrow-right-24: Learn about the Nendo Platform API Server](platform/server/index.md)
- [:octicons-arrow-right-24: Learn about the Nendo Platform Web Frontend](platform/web/index.md)