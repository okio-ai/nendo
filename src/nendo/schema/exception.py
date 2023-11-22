"""Schemas for common typed of nendo objects."""
from __future__ import annotations


class NendoError(Exception):
    """Base class for nendo errors."""

    def __init__(self, message):  # noqa: D107
        super().__init__(message)
        self.message = message


class NendoIdError(NendoError):
    """Nendo error with an additional details field."""

    def __init__(self, message, target_id):  # noqa: D107
        super().__init__(message)
        self.target_id = target_id


class NendoPluginError(NendoError):
    """Generic Plugin Error.

    Any custom plugin error should inherit from this.
    """


class NendoPluginConfigError(NendoPluginError):
    """Error related to the (mis)configuration of a plugin."""


class NendoPluginLoadingError(NendoPluginError):
    """Error related to loading of a plugin."""


class NendoPluginRuntimeError(NendoPluginError):
    """Generic plugin runtime error."""


class NendoLibraryError(NendoError):
    """Generic library error.

    All other library error inherit from this.
    """


class NendoStorageError(NendoLibraryError):
    """Generic storage error."""


class NendoResourceError(NendoError):
    """Error related to a Nendo resource."""

    def __init__(self, message, src):  # noqa: D107
        super().__init__(message)
        self.src = src

    def __str__(self):
        return f"Error with resource {self.src}. Details: {self.message}"


class NendoLibraryIdError(NendoLibraryError):
    """A library error that refers to an item with a specified id."""

    def __init__(self, message, target_id):  # noqa: D107
        super().__init__(message)
        self.target_id = target_id


class NendoUserNotFoundError(NendoLibraryIdError):
    """Error raised if a user was accessed that does not exist."""

    def __str__(self):
        return f"User with ID {self.target_id} not found."


class NendoTrackNotFoundError(NendoLibraryIdError):
    """Error raised if a track was accessed that does not exist."""

    def __str__(self):
        return f"Track with ID {self.target_id} not found."


class NendoBlobNotFoundError(NendoLibraryIdError):
    """Error raised if a blob was accessed that does not exist."""

    def __str__(self):
        return f"Blob with ID {self.target_id} not found."


class NendoCollectionNotFoundError(NendoLibraryIdError):
    """Error raised if a collection was accessed that does not exist."""

    def __str__(self):
        return f"Collection with ID {self.target_id} not found."


class NendoRelationshipNotFoundError(NendoLibraryError):
    """Error raised if a relationship does not exist beween two IDs."""

    def __init__(self, message, source_id, target_id):  # noqa: D107
        super().__init__(message)
        self.source_id = source_id
        self.target_id = target_id

    def __str__(self):
        return f"Relationship between {self.source_id} and {self.target_id} not found."


class NendoPluginDataNotFoundError(NendoLibraryIdError):
    """Error raised if a plugin data was accessed that does not exist."""

    def __str__(self):
        return f"Plugin data with ID {self.target_id} not found."


class NendoFileFormatError(NendoLibraryError):
    """Error raised if there is an error with the format of a processed file."""


class NendoMalformedIDError(NendoLibraryIdError):
    """Error raised if the given ID is malformed / does not represent a valid UUID."""

    def __str__(self):
        return f"Malformed ID {self.target_id}."


class NendoBucketNotFoundError(NendoStorageError):
    """A library error that refers to an item with a specified id."""

    def __init__(self, message, bucket_name):  # noqa: D107
        super().__init__(message)
        self.bucket_name = bucket_name

    def __str__(self):
        return f"Bucket with name {self.bucket_name} not found."
