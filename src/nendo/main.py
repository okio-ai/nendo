# -*- encoding: utf-8 -*-
"""Nendo core main class."""
from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import sys
from functools import lru_cache
from typing import List, Optional

from nendo import library as lib
from nendo import schema
from nendo.config import NendoConfig, get_settings

settings = get_settings()
nendo_logger = logging.getLogger("nendo")
log_fmt = "[%(asctime)s.%(msecs)03dZ] %(name)s         %(levelname)s %(message)s"


class Nendo:
    """Main class of the nendo framework."""

    _instance = None
    library: schema.NendoLibraryPlugin = None
    plugins: schema.NendoPluginRegistry = None
    logger: logging.Logger = None
    config: NendoConfig = None

    def __init__(
        self,
        config: Optional[NendoConfig] = None,
        plugins: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create a new nendo instance.

        Args:
            config (NendoConfig, optional): Custom settings to apply to this instance.
            plugins (str, optional): list of plugins to load. Defaults to None.
            logger (logging.Logger, optional): Logger to use. Defaults to none.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.logger = logger or nendo_logger
        self.config = config or settings
        self.plugins = schema.NendoPluginRegistry()
        plugin_names = plugins or self.config.plugins
        if self.config.log_file_path == "":
            logging.basicConfig(
                level=self.config.log_level.upper(),
                datefmt="%Y-%m-%dT%H:%M:%S",
                format=log_fmt,
            )
        else:
            if (
                not os.path.isdir(os.path.dirname(self.config.log_file_path))
                or os.path.basename(self.config.log_file_path) == ""
            ):
                self.logger.error(
                    "Config var log_file_path has been set but path is not "
                    "valid or no filename specified. Please fix your configuration.",
                )
                sys.exit(-1)
            logging.basicConfig(
                filename=self.config.log_file_path,
                level=self.config.log_level.upper(),
                datefmt="%Y-%m-%dT%H:%M:%S",
                format=log_fmt,
            )
        self._load_plugins(plugin_names=plugin_names)
        # initialize nendo library
        if self.config.library_plugin == "default":
            self.logger.info("Using DuckDBLibrary")
            self.library = lib.DuckDBLibrary(
                nendo_instance=self,
                config=self.config,
                logger=self.logger,
                plugin_name="DuckDBLibrary",
                plugin_version="0.1.0",
            )
        else:
            self.logger.info(f"Loading {self.config.library_plugin}")
            self.library = self._load_plugin(module_name=self.config.library_plugin)
        self._initialized = True

    # this turns the nendo class effectively into a singleton
    def __new__(cls, *args, **kwargs):  # noqa: D102, ARG003
        if not cls._instance:
            cls._instance = super(Nendo, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # this makes all library functions callable on the nendo instance itself
    def __getattr__(self, attr):
        if not hasattr(self.library, attr):
            raise AttributeError(f"Function '{attr}' unknown.")
        return getattr(self.library, attr)

    def _load_plugin(self, module_name: str) -> schema.NendoPlugin:
        package_spec = importlib.util.find_spec(module_name)
        if package_spec is not None:
            try:
                module_class = importlib.import_module(module_name)
                for cl in inspect.getmembers(module_class, inspect.isclass):
                    # NOTE currently, we only support one functional class per plugin
                    if issubclass(cl[1], schema.NendoPlugin):
                        self.logger.debug(
                            "Adding Nendo plugin %s from %s",
                            cl,
                            module_name,
                        )
                        plugin_name = cl[1].__name__
                        plugin_version = importlib.metadata.version(module_name)
                        plugin_instance: schema.NendoPlugin = getattr(
                            module_class,
                            plugin_name,
                        )(
                            nendo_instance=self,
                            config=self.config,
                            logger=self.logger,
                            plugin_name=module_name,
                            plugin_version=plugin_version,
                        )
                        return plugin_instance
            except Exception as e:  # noqa: BLE001
                raise schema.NendoPluginLoadingError(
                    f"Failed to import plugin '{module_name}'. Error: {e}",
                ) from None
        else:
            raise schema.NendoPluginLoadingError(
                f"Plugin {module_name} not installed in system. "
                "Please use e.g. pip to install it.",
            )

    def _load_plugins(self, plugin_names: List[str] = settings.plugins) -> None:
        """Load the specified nendo plugins."""
        for module_name in plugin_names:
            plugin_instance = self._load_plugin(module_name=module_name)
            self.plugins.add(
                plugin_name=plugin_instance.plugin_name,
                version=plugin_instance.plugin_version,
                plugin_instance=plugin_instance,
            )

        plugins_str = str(self.plugins)
        for line in plugins_str.split("\n"):
            self.logger.info(line)

    def __str__(self):
        output = "Nendo\n"
        output += "Config: "
        output += json.dumps(json.loads(self.config.json()), indent=4)
        # output += f"Library: {self.library}\n"
        output += f"\n{self.plugins}"
        return output


@lru_cache()
def get_nendo():
    """Get the nendo instance singledton, cached."""
    return Nendo()
