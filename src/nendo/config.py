"""Settings used to configure nendo."""
from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(Enum):
    """Enum used to denote the environment in which nendo is running."""

    LOCAL = "local"
    TEST = "test"
    REMOTE = "remote"


class NendoConfig(BaseSettings):
    """The basic nendo configuration object.

    Uses pydantic's settings management features. Refer to the
    [documentation page on configuration management](../usage/config.md) for
    a full list of configuration options.
    """

    environment: Environment = Field(default=Environment.LOCAL)
    log_level: str = Field(default="WARNING")
    log_file_path: str = Field(default="")
    plugins: List[str] = Field(default_factory=list)
    library_plugin: str = Field(default="default")
    library_path: str = Field(default="nendo_library")
    user_name: str = Field(default="nendo")
    user_id: str = Field(default="ffffffff-1111-2222-3333-1234567890ab")
    auto_resample: bool = Field(default=False)
    default_sr: int = Field(default=44100)
    copy_to_library: bool = Field(default=True)
    auto_convert: bool = Field(default=True)
    skip_duplicate: bool = Field(default=True)
    max_threads: int = Field(default=2)
    batch_size: int = Field(default=10)
    stream_mode: bool = Field(default=False)
    stream_chunk_size: int = Field(default=1)


@lru_cache()
def get_settings() -> NendoConfig:
    """Return the Nendo configuration, cached."""
    return NendoConfig()
