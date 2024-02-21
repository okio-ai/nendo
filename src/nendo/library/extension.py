# -*- encoding: utf-8 -*-
"""Extension classes of Nendo Core."""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel

from nendo.schema.exception import NendoLibraryError
from nendo.schema.plugin import NendoEmbeddingPlugin

if TYPE_CHECKING:
    import uuid

    from nendo.schema.core import (
        NendoCollection,
        NendoEmbedding,
        NendoEmbeddingBase,
        NendoTrack,
    )


class DistanceMetric(str, Enum):
    """Enum representing different types of resources used in Nendo."""

    euclidean: str = "l2"
    cosine: str = "cosine"
    max_inner_product: str = "inner"


class NendoLibraryVectorExtension(BaseModel):
    """Extension class to implement library plugins with vector support."""

    embedding_plugin: Optional[NendoEmbeddingPlugin] = None

    def __init__(  # noqa: D107
        self,
        embedding_plugin: Optional[str] = None,
        default_distance: DistanceMetric = DistanceMetric.cosine,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if embedding_plugin is not None:
            try:
                self.embedding_plugin = getattr(
                    self.nendo_instance.plugins,
                    embedding_plugin,
                )
            except AttributeError:
                self.logger.warning(
                    f"Plugin with name {embedding_plugin} has been configured "
                    "for the NendoLibraryVectorExtension but is not loaded. "
                    "Please make sure to install and enable the plugin "
                    "to use the embedding features of the nendo library.",
                )
        else:
            # try to auto-detect an embedding plugin from the registry
            self.embedding_plugin = self._get_embedding_plugin()
            if self.embedding_plugin is None:
                self.logger.warning(
                    "No embedding plugin was configured for the "
                    "NendoLibraryVectorExtension and none was found in the "
                    "PluginRegistry. Please make sure to install and enable one "
                    "to use the embedding features of the nendo library.",
                )
        self._default_distance = default_distance

    def _get_embedding_plugin(self):
        for registered_plugin in self.nendo_instance.plugins:
            # return the first embedding plugin found
            plugin = registered_plugin.plugin_instance
            if issubclass(plugin.__class__, NendoEmbeddingPlugin):
                self.logger.info(
                    f"Using {registered_plugin.name} as embedding plugin "
                    "for the NendoLibraryVectorExtension.",
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
        distance_metric: Optional[DistanceMetric] = None,
    ) -> float:
        """Compute the distance between two `NendoEmbedding` objects.

        If no distance metric is specified, the default distance metric
        configured upon extension initialization is used.

        Args:
            embedding1 (NendoEmbedding): The first embedding.
            embedding2 (NendoEmbedding): The second embedding.

        Raises:
            ValueError: If the chosen distance metric is unknown.

        Returns:
            float: The distance between the two embedding vectors.
        """
        metric = distance_metric or self._default_distance
        if metric == DistanceMetric.euclidean:
            return self.euclidean_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        if metric == DistanceMetric.cosine:
            return self.cosine_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        if metric == DistanceMetric.max_inner_product:
            return self.max_inner_product_distance(
                vec1=embedding1.embedding,
                vec2=embedding2.embedding,
            )
        raise ValueError(
            f"Got unexpected value for distance: {metric}. "
            f"Should be one of {', '.join([ds.value for ds in DistanceMetric])}.",
        )

    def cosine_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        """Compute the cosine distance between the two given vectors.

        Args:
            vec1 (npt.ArrayLike): The first vector.
            vec2 (npt.ArrayLike): The second vector.

        Raises:
            ValueError: If one of the vectors has zero norm, the cosine
                similarity is not defined and thus a `ValueError` is raised.

        Returns:
            float: The cosine distance between the two vectors.
        """
        dot_product = np.dot(vec1, vec2)
        norm_arr1 = np.linalg.norm(vec1)
        norm_arr2 = np.linalg.norm(vec2)
        norm_mult = norm_arr1 * norm_arr2
        if norm_mult == 0.0:
            raise ValueError("Division by zero in cosine similarity.")
        return dot_product / norm_mult

    def euclidean_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        """Compute the euclidean (L2) distance between the two given vectors.

        Args:
            vec1 (npt.ArrayLike): The first vector.
            vec2 (npt.ArrayLike): The second vector.

        Returns:
            float: The euclidean distance between the two vectors.
        """
        distance = np.linalg.norm(vec1 - vec2)
        return 1 / (1 + distance)

    def max_inner_product_distance(
        self,
        vec1: npt.ArrayLike,
        vec2: npt.ArrayLike,
    ) -> float:
        """Compute the maximum inner product distance between the two given vectors.

        Args:
            vec1 (npt.ArrayLike): The first vector.
            vec2 (npt.ArrayLike): The second vector.

        Returns:
            float: The maximum inner product distance between the two vectors.
        """
        return np.max(np.inner(vec1, vec2))

    # Embedding management functions

    def embed_text(self, text: str) -> npt.ArrayLike:
        """Embed the given text using the library's default embedding plugin.

        Args:
            text (str): The text to be embedded.

        Raises:
            NendoLibraryError: If not embedding plugin has been loaded.

        Returns:
            npt.ArrayLike: The embedding vector corresponding to the text.
        """
        if self.embedding_plugin is not None:
            _, emb = self.embedding_plugin(text=text)
            return emb
        raise NendoLibraryError("No embedding plugin loaded. Cannot embed track.")

    def embed_track(self, track: NendoTrack) -> NendoEmbedding:
        """Embed the given track using the library's default embedding plugin.

        Args:
            track (NendoTrack): The track to be embedded.

        Raises:
            NendoLibraryError: If not embedding plugin has been loaded.

        Returns:
            NendoEmbedding: The object representing the track embedding.
        """
        if self.embedding_plugin is not None:
            return self.embedding_plugin(track=track)
        raise NendoLibraryError("No embedding plugin loaded. Cannot embed track.")

    def embed_collection(self, collection: NendoCollection) -> List[NendoEmbedding]:
        """Embed the given collection using the library's default embedding plugin.

        Args:
            collection (NendoCollection): The collection to be embedded.

        Raises:
            NendoLibraryError: If not embedding plugin has been loaded.

        Returns:
            List[NendoEmbedding]: A list of embeddings corresponding to the
                collection's tracks.
        """
        if self.embedding_plugin is not None:
            return self.embedding_plugin(collection=collection)
        raise NendoLibraryError("No embedding plugin loaded. Cannot embed Collection.")

    # Query / retrieval functions

    def nearest_by_vector(
        self,
        vec: npt.ArrayLike,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[List[str]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        """Obtain the n nearest neighboring tracks to a vector from the library.

        Args:
            vec (numpy.typing.ArrayLike): The vector from which to start the neighbor search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                currently configured embedding plugin for the library vector extension
                is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the
                version of the currently configured embedding plugin for the library
                vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[NendoTrack]: The list of tracks corresponding to the n nearest
                embedding vectors of the given target vector.
        """
        tracks_and_scores = self.get_similar_by_vector_with_score(
            vec=vec,
            limit=limit,
            offset=offset,
            filters=filters,
            search_meta=search_meta,
            track_type=track_type,
            user_id=user_id,
            collection_id=collection_id,
            plugin_names=plugin_names,
            embedding_name=embedding_name,
            embedding_version=embedding_version,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_track(
        self,
        track: NendoTrack,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[Dict[str, List[str]]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        """Obtain the n nearest neighboring tracks to a track from the library.

        Args:
            track (NendoTrack): The track from which to start the neighbor search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                first embedding found for that track is used. If no embedding exists,
                the name of the currently configured embedding plugin for the library
                vector extension is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the name
                of the first embedding found for that track is used. If no embedding
                exists,the version of the currently configured embedding plugin for
                the library vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[NendoTrack]: The list of tracks corresponding to the n nearest
                embedding vectors of the given target track.
        """
        tracks_and_scores = self.nearest_by_track_with_score(
            track=track,
            limit=limit,
            offset=offset,
            filters=filters,
            search_meta=search_meta,
            track_type=track_type,
            user_id=user_id,
            collection_id=collection_id,
            plugin_names=plugin_names,
            embedding_name=embedding_name,
            embedding_version=embedding_version,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_track_with_score(
        self,
        track: NendoTrack,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[Dict[str, List[str]]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        """Obtain the n nearest neighbors to a track, together with their distances.

        Args:
            track (NendoTrack): The track from which to start the neighbor search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                first embedding found for that track is used. If no embedding exists,
                the name of the currently configured embedding plugin for the library
                vector extension is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the name
                of the first embedding found for that track is used. If no embedding
                exists,the version of the currently configured embedding plugin for
                the library vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[Tuple[NendoTrack, float]]: List of tuples containing a track in
                the first position and their distance ("score") in the second
                position, ordered by their distance in ascending order.
        """
        plugin_name = (
            embedding_name
            if embedding_name is not None
            else (
                self.embedding_plugin.plugin_name
                if self.embedding_plugin is not None
                else None
            )
        )
        plugin_version = (
            embedding_version
            if embedding_version is not None
            else (
                self.embedding_plugin.plugin_version
                if self.embedding_plugin is not None
                else None
            )
        )
        track_embeddings = self.get_embeddings(
            track_id=track.id,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
        )
        if len(track_embeddings) < 1:
            track_embedding = self.embed_track(track)
        else:
            track_embedding = track_embeddings[0]
            plugin_name = track_embedding.plugin_name
            plugin_version = track_embedding.plugin_version

        nearest = self.nearest_by_vector_with_score(
            vec=track_embedding.embedding,
            limit=limit + 1,
            offset=offset,
            filters=filters,
            search_meta=search_meta,
            track_type=track_type,
            user_id=user_id,
            collection_id=collection_id,
            plugin_names=plugin_names,
            embedding_name=plugin_name,
            embedding_version=plugin_version,
            distance_metric=distance_metric,
        )
        return nearest[1:]

    def nearest_by_query(
        self,
        query: str,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[List[str]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[NendoTrack]:
        """Obtain the n nearest neighboring tracks to a query string.

        Args:
            query (str): The query from which to start the neighbor search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                currently configured embedding plugin for the library vector extension
                is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the
                version of the currently configured embedding plugin for the library
                vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[NendoTrack]: The list of tracks corresponding to the n nearest
                embedding vectors of the given query string.
        """
        tracks_and_scores = self.nearest_by_query_with_score(
            query=query,
            limit=limit,
            offset=offset,
            filters=filters,
            search_meta=search_meta,
            track_type=track_type,
            user_id=user_id,
            collection_id=collection_id,
            plugin_names=plugin_names,
            embedding_name=embedding_name,
            embedding_version=embedding_version,
            distance_metric=distance_metric,
        )
        return [track for track, _ in tracks_and_scores]

    def nearest_by_query_with_score(
        self,
        query: str,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[List[str]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        """Obtain the n nearest neighboring tracks to a query, together with scores.

        Args:
            query (str): The query from which to start the neighbor search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                currently configured embedding plugin for the library vector extension
                is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the
                version of the currently configured embedding plugin for the library
                vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[Tuple[NendoTrack, float]]: List of tuples containing a track in
                the first position and their distance ("score") in the second
                position, ordered by their distance in ascending order.
        """
        query_embedding = self.embed_text(query)
        return self.nearest_by_vector_with_score(
            vec=query_embedding,
            limit=limit,
            offset=offset,
            filters=filters,
            search_meta=search_meta,
            track_type=track_type,
            user_id=user_id,
            collection_id=collection_id,
            plugin_names=plugin_names,
            embedding_name=embedding_name,
            embedding_version=embedding_version,
            distance_metric=distance_metric,
        )

    # =================================
    # Implementation-specific functions
    # =================================

    # implementation of distance metrics
    @property
    @abstractmethod
    def distance_metric(self):
        """Return a function that computes the default distance metric.."""

    # Basic embedding management functions

    @abstractmethod
    def add_embedding(
        self,
        embedding: NendoEmbeddingBase,
    ) -> NendoEmbedding:
        """Add a new embedding to the library.

        Args:
            embedding (NendoEmbeddingBase): The embedding to add.

        Returns:
            NendoEmbedding: The added embedding.
        """
        raise NotImplementedError

    @abstractmethod
    def get_embedding(
        self,
        embedding_id: uuid.UUID,
    ) -> Optional[NendoEmbedding]:
        """Retrieve a specific embedding from the library.

        Args:
            embedding_id (uuid.UUID): ID of the embedding to retrieve.

        Returns:
            Optional[NendoEmbedding]: The embedding if the ID was found.
                None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_embeddings(
        self,
        track_id: Optional[uuid.UUID] = None,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
    ) -> List[NendoEmbedding]:
        """Get a list of embeddings by filtering for track ID and plugin specifics.

        Args:
            track_id (Optional[uuid.UUID], optional): The track ID to which the
                embeddings should be related. Defaults to None.
            plugin_name (Optional[str], optional): The name of the plugin used to
                create the embeddings. Defaults to None.
            plugin_version (Optional[str], optional): The version of the plugin used
                to create the embeddings. Defaults to None.

        Returns:
            List[NendoEmbedding]: List of embeddings that fulfill the defined filter
                criteria.
        """
        raise NotImplementedError

    @abstractmethod
    def update_embedding(
        self,
        embedding: NendoEmbedding,
    ) -> NendoEmbedding:
        """Update an existing embedding in the library.

        Args:
            embedding (NendoEmbedding): The updated embedding.

        Returns:
            NendoEmbedding: The updated embedding.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_embedding(self, embedding_id: uuid.UUID) -> bool:
        """Remove an embedding from the library.

        Args:
            embedding_id (uuid.UUID): The ID of the embedding to remove.

        Returns:
            bool: True if the embedding was successfully removed, False otherwise.
        """
        raise NotImplementedError

    # Distance-based retrieval functions

    def nearest_by_vector_with_score(
        self,
        vec: npt.ArrayLike,
        limit: int = 10,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[Dict[str, List[str]]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        embedding_name: Optional[str] = None,
        embedding_version: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[Tuple[NendoTrack, float]]:
        """Obtain the n nearest neighbors to a vector, together with their distances.

        Args:
            vec (numpy.typing.ArrayLike): The vector from which to start the neighbor
                search.
            limit (int): Limit the number of returned results. Default is 10.
            offset (Optional[int]): Offset into the paginated results (requires limit).
            filters (Optional[dict]): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            embedding_name (str, optional): Name of the embedding plugin for which to
                retrieve and compare the vectors. If none is given, the name of the
                currently configured embedding plugin for the library vector extension
                is used.
            embedding_version (str, optional): Version of the embedding plugin for
                which to retrieve and compare the vectors. If none is given, the
                version of the currently configured embedding plugin for the library
                vector extension is used.
            distance_metric (Optional[DistanceMetric], optional): The distance metric
                to use. Defaults to None.

        Returns:
            List[Tuple[NendoTrack, float]]: List of tuples containing a track in
                the first position and their distance ("score") in the second
                position, ordered by their distance in ascending order.
        """
        raise NotImplementedError
