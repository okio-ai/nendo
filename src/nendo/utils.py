"""Utility functions used by Nendo."""
import hashlib
import logging
import uuid
from abc import ABC
from typing import Callable, ClassVar, List, Optional, Union

import numpy as np
import sounddevice as sd

logger = logging.getLogger("nendo")


def get_wrapped_methods(plugin_class: ABC) -> List[Callable]:
    """Get all wrapped methods of the given plugin class."""
    return [
        f
        for f in type(plugin_class).__dict__.values()
        if hasattr(f, "__wrapped__") and "pydantic" not in f.__name__
    ]


def md5sum(file_path):
    """Compute md5 checksum of file found under the given file_path."""
    hash_md5 = hashlib.md5()  # noqa: S324
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def play_signal(signal: np.ndarray, sr: int, loop: bool = False):
    """Play the signal given as numpy array using `sounddevice`."""
    logger.info("Playing signal with sample rate %d...", sr)

    # sounddevice wants the signal to be in the shape (n_samples, n_channels)
    sd.play(signal.T, samplerate=sr, loop=loop, blocking=True)
    sd.wait()


def ensure_uuid(target_id: Optional[Union[str, uuid.UUID]] = None) -> uuid.UUID:
    """Take a string or a UUID and return the same value as a guaranteed UUID.

    Args:
        target_id (Union[str, uuid.UUID]): The target ID to convert to UUID type.

    Returns:
        uuid.UUID: The given target_id, converted to UUID. None if None was passed.
    """
    if target_id is not None and isinstance(target_id, str) and target_id != "":
        return uuid.UUID(target_id)
    if isinstance(target_id, uuid.UUID):
        return target_id
    return None


class AudioFileUtils:
    """Utility class for handling audio files."""

    supported_filetypes: ClassVar[List[str]] = [
        "wav",
        "mp3",
        "aiff",
        "flac",
        "ogg",
    ]

    def is_supported_filetype(self, filepath: str) -> bool:
        """Check if the filetype of the given file is supported by Nendo."""
        return filepath.lower().split(".")[-1] in self.supported_filetypes


def pretty_print(data, indent=0):
    """Helper function for pretty printing."""
    result = ""
    if isinstance(data, dict):
        for key, value in data.items():
            result += "\t" * indent + str(key) + ": "
            if isinstance(value, (dict, list)):
                result += "\n" + pretty_print(value, indent + 1)
            else:
                result += str(value) + "\n"
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                result += pretty_print(item, indent + 1)
            else:
                result += "\t" * indent + str(item) + "\n"
    return result
