# -*- encoding: utf-8 -*-
"""Extension classes of Nendo Core."""
from __future__ import annotations

import uuid
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
import numpy.typing as npt

from nendo.schema.core import (
    NendoCollection,
    NendoEmbedding,
    NendoEmbeddingBase,
    NendoTrack,
)
from nendo.schema.exception import NendoPluginLoadingError
from nendo.schema.plugin import NendoEmbeddingPlugin


class DistanceMetric(str, Enum):
    """Enum representing different types of resources used in Nendo."""

    euclidean: str = "l2"
    cosine: str = "cosine"
    max_inner_product: str = "inner"


class NendoLibraryVectorExtension(metaclass=ABCMeta):
    """Extension class to implement library plugins with vector support."""

    def __init__(
        self,
        embedding_plugin: Optional[str] = None,
        default_distance: DistanceMetric = DistanceMetric.cosine,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if embedding_plugin is not None:
            try:
                self.embedding_plugin = getattr(
                    self.nendo_instance.plugins, embedding_plugin
                )
            except AttributeError as e:
                self.logger.error(e)
                raise NendoPluginLoadingError(
                    f"Plugin with name {embedding_plugin} has been configured for the "
                    "NendoLibraryVectorExtension but is not loaded. Please load the plugin "
                    "or change the library configuration.",
                ) from None
        else:
            # try to auto-detect an embedding plugin from the registry
            self.embedding_plugin = self._get_embedding_plugin()
            if self.embedding_plugin is None:
                raise NendoPluginLoadingError(
                    "No embedding plugin was configured for the "
                    "NendoLibraryVectorExtension and none was found in the "
                    "PluginRegistry. Please make sure to enable at least one "
                    "EmbeddingPlugin when using a NendoLibrary with vector support.",
                )
        self._default_distance = default_distance

    def _get_embedding_plugin(self):
        for registered_plugin in self.nendo_instance.plugins:
            # return the first embedding plugin found
            plugin = registered_plugin.plugin_instance
            if isinstance(plugin, NendoEmbeddingPlugin):
                self.logger.info(
                    f"Using {registered_plugin.name} as embedding plugin "
                    "for the NendoLibraryVectorExtension."
                )
                return plugin
        return None

    # =================
    # General functions
    # =================

    # Vector distance functions

    def embedding_distance(
        self,
        embedding1: NendoEmbedding,
        embedding2: NendoEmbedding,
    ) -> float:
        if self._default_distance == DistanceMetric.euclidean:
            return self.euclidean_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        if self._default_distance == DistanceMetric.cosine:
            return self.cosine_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        if self._default_distance == DistanceMetric.max_inner_product:
            return self.max_inner_product_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        raise ValueError(
            f"Got unexpected value for distance: {self._default_distance}. "
            f"Should be one of {', '.join([ds.value for ds in DistanceMetric])}.",
        )

    def cosine_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        dot_product = np.dot(vec1, vec2)
        norm_arr1 = np.linalg.norm(vec1)
        norm_arr2 = np.linalg.norm(vec2)
        return dot_product / (norm_arr1 * norm_arr2)

    def euclidean_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        distance = np.linalg.norm(vec1 - vec2)
        return 1 / (1 + distance)

    def max_inner_product_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        return np.max(np.inner(vec1, vec2))

    # Embedding management functions

    def embed_text(self, text: str) -> NendoEmbedding:
        return self.embed_text(text=text)

    def embed_track(self, track: NendoTrack) -> NendoEmbedding:
        return self.embedding_plugin(track=track)

    def embed_collection(self, collection: NendoCollection) -> List[NendoEmbedding]:
        return self.embedding_plugin(collection=collection)

    # Query / retrieval functions

    def nearest_by_vector(
        self,
        vec: npt.ArrayLike,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        tracks_and_scores = self.get_similar_by_vector_with_score(
            vec=vec,
            n=n,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_track(
        self,
        track: NendoTrack,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        tracks_and_scores = self.nearest_by_track_with_score(
            track=track,
            n=n,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_track_with_score(
        self,
        track: NendoTrack,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        track_embedding = self.get_embedding_by_track_id(track.id)
        if track_embedding is None:
            track_embedding = self.embed_track(track)
        return self.nearest_by_vector_with_score(
            vec=track_embedding.embedding,
            n=n,
            distance_metric=distance_metric,
        )

    def nearest_by_query(
        self,
        query: str,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        tracks_and_scores = self.nearest_by_query_with_score(
            query=query,
            n=n,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_query_with_score(
        self,
        query: str,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        query_embedding = self.embed_text(query)
        return self.nearest_by_vector_with_score(
            vec=query_embedding.embedding,
            n=n,
            distance_metric=distance_metric,
        )

    # =================================
    # Implementation-specific functions
    # =================================

    # implementation of distance metrics
    @property
    @abstractmethod
    def distance_metric(self):
        pass

    # Basic embedding management functions

    @abstractmethod
    def add_embedding(
        self,
        embedding: NendoEmbeddingBase,
    ) -> NendoEmbedding:
        raise NotImplementedError

    @abstractmethod
    def get_embedding(
        self,
        embedding_id: uuid.UUID,
    ) -> Optional[NendoEmbedding]:
        raise NotImplementedError

    @abstractmethod
    def get_embeddings(
        self,
        track_id: Optional[uuid.UUID] = None,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
    ) -> List[NendoEmbedding]:
        raise NotImplementedError

    @abstractmethod
    def update_embedding(
        self,
        embedding: NendoEmbedding,
    ) -> NendoEmbedding:
        raise NotImplementedError

    @abstractmethod
    def remove_embedding(self, embedding_id: uuid.UUID) -> bool:
        raise NotImplementedError

    # Distance-based retrieval functions

    def nearest_by_vector_with_score(
        self,
        vec: npt.ArrayLike,
        n: int = 5,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        raise NotImplementedError
