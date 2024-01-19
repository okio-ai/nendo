# -*- encoding: utf-8 -*-
# ruff: noqa: F401
"""The Nendo AI Audio Tool Suite."""

from importlib import metadata

from .config import NendoConfig
from .library import (
    CollectionCollectionRelationshipDB,
    DistanceMetric,
    DuckDBLibrary,
    NendoBlobDB,
    NendoCollectionDB,
    NendoLibraryVectorExtension,
    NendoPluginDataDB,
    NendoTrackDB,
    SqlAlchemyNendoLibrary,
    TrackCollectionRelationshipDB,
    TrackTrackRelationshipDB,
)
from .main import Nendo
from .schema import (
    NendoAnalysisPlugin,
    NendoBucketNotFoundError,
    NendoCollection,
    NendoCollectionNotFoundError,
    NendoCollectionSlim,
    NendoEffectPlugin,
    NendoEmbedding,
    NendoEmbeddingBase,
    NendoEmbeddingCreate,
    NendoEmbeddingPlugin,
    NendoError,
    NendoFileFormatError,
    NendoGeneratePlugin,
    NendoIdError,
    NendoLibraryError,
    NendoLibraryIdError,
    NendoLibraryPlugin,
    NendoPlugin,
    NendoPluginConfigError,
    NendoPluginData,
    NendoPluginDataNotFoundError,
    NendoPluginError,
    NendoPluginLoadingError,
    NendoPluginRuntimeError,
    NendoRelationshipNotFoundError,
    NendoResource,
    NendoStorage,
    NendoStorageError,
    NendoStorageLocalFS,
    NendoTrack,
    NendoTrackNotFoundError,
    NendoTrackSlim,
    NendoUser,
    NendoUserNotFoundError,
    NendoUtilityPlugin,
    ResourceLocation,
)

meta = metadata.metadata(__package__ or __name__)

__version__ = meta["Version"]
__author__ = meta["Author"]
__email__ = meta["Author-email"]
__description__ = meta["Description"]
__url__ = meta["Project-URL"]
