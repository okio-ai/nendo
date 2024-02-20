# -*- encoding: utf-8 -*-
"""Plugin classes of Nendo Core."""
from __future__ import annotations

import functools
import inspect
import os
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

import numpy as np
from pydantic import ConfigDict, DirectoryPath, FilePath

from nendo.schema.core import (
    NendoBlob,
    NendoCollection,
    NendoEmbedding,
    NendoPlugin,
    NendoPluginData,
    NendoStorage,
    NendoTrack,
    Visibility,
)
from nendo.schema.exception import NendoError, NendoPluginRuntimeError
from nendo.utils import ensure_uuid, get_wrapped_methods

if TYPE_CHECKING:
    import uuid


class NendoAnalysisPlugin(NendoPlugin):
    """Basic class for nendo analysis plugins.

    Analysis plugins are plugins that analyze a track or a collection
    and add metadata and other properties to the track or collection.
    Decorate your methods with `@NendoAnalysisPlugin.plugin_data` to add the
    return values of your methods as plugin data to the track or collection.

    Decorate your methods with `@NendoAnalysisPlugin.run_track` to run your method
    on a track and use `@NendoAnalysisPlugin.run_collection` to run your method on
    a collection.

    Examples:
        ```python
        from nendo import Nendo, NendoConfig

        class MyPlugin(NendoAnalysisPlugin):
            ...

            @NendoAnalysisPlugin.plugin_data
            def my_plugin_data_function_one(self, track):
                # do something analysis on the track
                return {"key": "value"}

            @NendoAnalysisPlugin.plugin_data
            def my_plugin_data_function_two(self, track):
                # do some more analysis on the track
                return {"key": "value"}

            @NendoAnalysisPlugin.run_track
            def my_run_track_function(self, track):
                my_plugin_data_function_one(track)
                my_plugin_data_function_two(track)
        ```
    """

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "AnalysisPlugin"

    # decorators
    # ----------
    @staticmethod
    def plugin_data(
        func: Callable[[NendoPlugin, NendoTrack], Dict[str, Any]],
    ) -> Callable[[NendoPlugin, NendoTrack], Dict[str, Any]]:
        """Decorator to enrich a NendoTrack with data from a plugin.

        Args:
            func: Callable[[NendoPlugin, NendoTrack], Dict[str, Any]]: The function to register.

        Returns:
            Callable[[NendoPlugin, NendoTrack], Dict[str, Any]]: The wrapped function.
        """

        def wrapper(self, track: NendoTrack):
            try:
                f_result = func(self, track)
            except NendoError as e:
                raise NendoPluginRuntimeError(
                    f"Error running plugin function: {e}",
                ) from None
            for k, v in f_result.items():
                track.add_plugin_data(
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    key=str(k),
                    value=v,
                )
            return f_result

        return wrapper

    @staticmethod
    def run_collection(
        func: Callable[[NendoPlugin, NendoCollection, Any], None],
    ) -> Callable[[NendoPlugin, Any], NendoCollection]:
        """Decorator to register a function as a collection running function for a `NendoAnalysisPlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoCollection, Any], None]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> NendoCollection:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if isinstance(track_or_collection, NendoCollection):
                func(self, track_or_collection, **kwargs)
                return self.nendo_instance.library.get_collection(
                    track_or_collection.id,
                )

            tmp_collection = self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track_or_collection.id],
                collection_type="temp",
            )
            func(self, tmp_collection, **kwargs)
            return self.nendo_instance.library.get_track(track_or_collection.id)

        return wrapper

    @staticmethod
    def run_track(
        func: Callable[[NendoPlugin, NendoTrack, Any], None],
    ) -> Callable[[NendoPlugin, Any], Union[NendoTrack, NendoCollection]]:
        """Decorator to register a function as a track running function for a `NendoAnalysisPlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoTrack, Any], None]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if isinstance(track_or_collection, NendoTrack):
                func(self, track_or_collection, **kwargs)
                return self.nendo_instance.library.get_track(track_or_collection.id)
            [func(self, track, **kwargs) for track in track_or_collection.tracks()]
            return self.nendo_instance.library.get_collection(track_or_collection.id)

        return wrapper


class NendoGeneratePlugin(NendoPlugin):
    """Basic class for nendo generate plugins.

    Generate plugins are plugins that generate new tracks or collections,
    either from scratch or based on existing tracks or collections.
    Decorate your methods with `@NendoGeneratePlugin.run_track` to run your method
    on a track, use `@NendoGeneratePlugin.run_collection` to run your method on
    a collection and use `@NendoGeneratePlugin.run_signal` to run your method on
    a signal.

    Examples:
        ```python
        from nendo import Nendo, NendoConfig

        class MyPlugin(NendoGeneratePlugin):
            ...

            @NendoAnalysisPlugin.run_track
            def my_generate_track_function(self, track, arg_one="foo"):
                # generate some new audio

                # add audio to the nendo library
                return self.nendo_instance.library.add_related_track_from_signal(
                    signal,
                    sr,
                    related_track_id=track.id,
                )
        ```
    """

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "GeneratePlugin"

    @staticmethod
    def run_collection(
        func: Callable[[NendoPlugin, Optional[NendoCollection], Any], NendoCollection],
    ) -> Callable[[NendoPlugin, Any], NendoCollection]:
        """Decorator to register a function as a collection running function for a `NendoGeneratePlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoCollection, Any], NendoCollection]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> NendoCollection:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if track_or_collection is None:
                return func(self, **kwargs)

            if isinstance(track_or_collection, NendoCollection):
                return func(self, track_or_collection, **kwargs)

            tmp_collection = self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track_or_collection.id],
                collection_type="temp",
            )
            return func(self, tmp_collection, **kwargs)

        return wrapper

    @staticmethod
    def run_signal(
        func: Callable[
            [NendoPlugin, Optional[np.ndarray], Optional[int], Any],
            Tuple[np.ndarray, int],
        ],
    ) -> Callable[[NendoPlugin, Any], Union[NendoTrack, NendoCollection]]:
        """Decorator to register a function as a signal running function for a `NendoGeneratePlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, np.ndarray, int, Any], Tuple[np.ndarray, int]]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if track_or_collection is None:
                signal, sr = func(self, **kwargs)
                return self.nendo_instance.library.add_track_from_signal(
                    signal,
                    sr,
                )
            if isinstance(track_or_collection, NendoTrack):
                signal, sr = track_or_collection.signal, track_or_collection.sr
                new_signal, new_sr = func(self, signal, sr, **kwargs)
                return self.nendo_instance.library.add_related_track_from_signal(
                    new_signal,
                    sr,
                    related_track_id=track_or_collection.id,
                )
            processed_tracks = []
            for track in track_or_collection.tracks():
                new_signal, new_sr = func(
                    self,
                    track.signal,
                    track.sr,
                    **kwargs,
                )
                processed_tracks.append(
                    self.nendo_instance.library.add_related_track_from_signal(
                        new_signal,
                        track.sr,
                        related_track_id=track.id,
                    ),
                )
            return self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track.id for track in processed_tracks],
                collection_type="temp",
            )

        return wrapper

    @staticmethod
    def run_track(
        func: Callable[
            [NendoPlugin, Optional[NendoTrack], Any],
            Union[NendoTrack, List[NendoTrack]],
        ],
    ) -> Callable[[NendoPlugin, Any], Union[NendoTrack, NendoCollection]]:
        """Decorator to register a function as a track running function for a `NendoGeneratePlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoTrack, Any], Union[NendoTrack, List[NendoTrack]]]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            processed_tracks = []
            if track_or_collection is None:
                track = func(self, **kwargs)

                # may be multiple tracks as a result
                if not isinstance(track, list):
                    return track
                processed_tracks.extend(track)
            elif isinstance(track_or_collection, NendoTrack):
                track = func(self, track_or_collection, **kwargs)

                # may be multiple tracks as a result
                if not isinstance(track, list):
                    return track
                processed_tracks.extend(track)
            else:
                for track in track_or_collection.tracks():
                    processed_track = func(self, track, **kwargs)

                    # may be multiple tracks as a result
                    if isinstance(processed_track, list):
                        processed_tracks.extend(processed_track)
                    else:
                        processed_tracks.append(processed_track)

            return self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track.id for track in processed_tracks],
                collection_type="temp",
            )

        return wrapper


class NendoEffectPlugin(NendoPlugin):
    """Basic class for nendo effects plugins.

    Effects plugins are plugins that add effects to tracks or collections.
    Decorate your methods with `@NendoGeneratePlugin.run_track` to run your method
    on a track, use `@NendoGeneratePlugin.run_collection` to run your method on
    a collection and use `@NendoGeneratePlugin.run_signal` to run your method on
    a signal.

    Examples:
        ```python
        from nendo import Nendo, NendoConfig

        class MyPlugin(NendoGeneratePlugin):
            ...

            @NendoAnalysisPlugin.run_signal
            def my_effect_function(self, signal, sr, arg_one="foo"):
                # add some effect to the signal
                new_signal = apply_effect(signal, sr, arg_one)

                return new_signal, sr
        ```
    """

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "EffectPlugin"

    @staticmethod
    def run_collection(
        func: Callable[[NendoPlugin, NendoCollection, Any], NendoCollection],
    ) -> Callable[[NendoPlugin, Any], NendoCollection]:
        """Decorator to register a function as a collection running function for a `NendoEffectPlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoCollection, Any], NendoCollection]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoCollection]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> NendoCollection:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if isinstance(track_or_collection, NendoCollection):
                return func(self, track_or_collection, **kwargs)

            tmp_collection = self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track_or_collection.id],
                collection_type="temp",
            )
            return func(self, tmp_collection, **kwargs)

        return wrapper

    @staticmethod
    def run_signal(
        func: Callable[[NendoPlugin, np.ndarray, int, Any], Tuple[np.ndarray, int]],
    ) -> Callable[[NendoPlugin, Any], Union[NendoTrack, NendoCollection]]:
        """Decorator to register a function as a signal running function for a `NendoEffectPlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, np.ndarray, int, Any], Tuple[np.ndarray, int]]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoTrack]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            processed_tracks = []
            if isinstance(track_or_collection, NendoTrack):
                signal, sr = track_or_collection.signal, track_or_collection.sr
                new_signal, new_sr = func(self, signal, sr, **kwargs)

                # TODO update track instead of adding a new one to the library
                return self.nendo_instance.library.add_related_track_from_signal(
                    new_signal,
                    sr,
                    related_track_id=track_or_collection.id,
                )

            for track in track_or_collection.tracks():
                new_signal, new_sr = func(
                    self,
                    track.signal,
                    track.sr,
                    **kwargs,
                )

                # TODO update track instead of adding a new one to the library
                processed_tracks.append(
                    self.nendo_instance.library.add_related_track_from_signal(
                        new_signal,
                        track.sr,
                        related_track_id=track.id,
                    ),
                )

            return self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track.id for track in processed_tracks],
                collection_type="temp",
            )

        return wrapper

    @staticmethod
    def run_track(
        func: Callable[
            [NendoPlugin, NendoTrack, Any],
            Union[NendoTrack, List[NendoTrack]],
        ],
    ) -> Callable[[NendoPlugin, Any], NendoTrack]:
        """Decorator to register a function as a track running function for a `NendoEffectPlugin`.

        This decorator wraps the function and allows a plugin user to call the plugin with either a collection or a track.

        Args:
            func: Callable[[NendoPlugin, NendoTrack, Any], Union[NendoTrack, List[NendoTrack]]]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], NendoTrack]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if isinstance(track_or_collection, NendoTrack):
                return func(self, track_or_collection, **kwargs)

            processed_tracks = [
                func(self, track, **kwargs) for track in track_or_collection.tracks()
            ]
            return self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track.id for track in processed_tracks],
                collection_type="temp",
            )

        return wrapper


class NendoEmbeddingPlugin(NendoPlugin):
    """Basic class for nendo embedding plugins.

    Embedding plugins are plugins that are used by nendo to embed NendoTracks
    or query strings into an n-dimensional vector space. To implement such a
    plugin, at least one function should exist that is annotated with the `@run_text`
    decorator. Alternatively or in addition to, any of the other decorators,
    `@run_signal_and_text`, `@run_track`, and `@run_collection` can be implemented
    and will be used when the plugin is directly called.
    """

    def track_to_text(self, track: NendoTrack) -> str:
        """Convert the given track into a string.

        Can be used by embedding plugins to avoid implementing their own
        track-to-string conversion.

        Args:
            track (NendoTrack): The track to be converted.

        Returns:
            str: The string representation of the given track.
        """
        text = ""
        meta_items = [
            "artist",
            "album",
            "title",
            "genre",
            "year",
            "duration",
            "content",
        ]
        for i in meta_items:
            if track.get_meta(i) is not None:
                text += f"{i}: {track.get_meta(i)}; "
        for pd in track.get_plugin_data():
            text += f"{pd.key}: {pd.value}; "
        return text

    @staticmethod
    def run_text(
        func: Callable[[NendoPlugin, str, Any], Tuple[str, np.ndarray]],
    ) -> Callable[
        [NendoPlugin, Any],
        Union[Tuple[str, np.ndarray], NendoEmbedding, List[NendoEmbedding]],
    ]:
        """Decorator to register a function that embeds a given text string into a vector space.

        This decorator wraps the function and allows a plugin user to call the plugin with either a text, a track, or a collection.

        Args:
            func: Callable[[NendoPlugin, str, Any], Tuple[str, np.ndarray]]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], Union[[str, np.ndarray], NendoEmbedding, List[NendoEmbedding]]]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(
            self,
            **kwargs: Any,
        ) -> Union[Tuple[str, np.ndarray], NendoEmbedding, List[NendoEmbedding]]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if track_or_collection is None:
                kwargs.pop("signal", None)
                kwargs.pop("sr", None)
                text, embedding_vector = func(self, **kwargs)
                return text, embedding_vector
            if isinstance(track_or_collection, NendoTrack):
                text, embedding_vector = func(
                    self,
                    text=self.track_to_text(track=track_or_collection),
                    **kwargs,
                )
                embedding = NendoEmbedding(
                    track_id=track_or_collection.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                return embedding
            processed_tracks = []
            for track in track_or_collection.tracks():
                text, embedding_vector = func(
                    self,
                    text=self.track_to_text(track=track),
                    **kwargs,
                )
                embedding = NendoEmbedding(
                    track_id=track.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                processed_tracks.append(embedding)
            return processed_tracks

        return wrapper

    @staticmethod
    def run_signal_and_text(
        func: Callable[[NendoPlugin, np.array, int, str, Any], None],
    ) -> Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]:
        """Decorator to register a function as a function to create a `NendoEmbedding` from a given signal, sr, and text.

        This decorator wraps the function and allows a plugin user to call the plugin with either a set of (signal, sr, text), a track or a collection.

        Args:
            func: Callable[[NendoPlugin, np.array, int, str, Any], None]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoEmbedding, List[NendoEmbedding]]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if track_or_collection is None:
                signal = kwargs.get("signal", None)
                sr = kwargs.get("sr", None)
                text, embedding_vector = func(self, **kwargs)
                new_track = self.nendo_instance.library.add_track_from_signal(
                    signal=signal if signal is not None else np.array([]),
                    sr=sr if sr is not None else self.config.default_sr,
                )
                embedding = NendoEmbedding(
                    track_id=new_track.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                return embedding
            if isinstance(track_or_collection, NendoTrack):
                kwargs["signal"] = track_or_collection.signal
                kwargs["sr"] = track_or_collection.sr
                kwargs["text"] = self.track_to_text(track=track_or_collection)
                text, embedding_vector = func(self, **kwargs)
                embedding = NendoEmbedding(
                    track_id=track_or_collection.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                return embedding
            embeddings = []
            for track in track_or_collection.tracks():
                kwargs["signal"] = track.signal
                kwargs["sr"] = track.sr
                kwargs["text"] = self.track_to_text(track=track)
                text, embedding_vector = func(self, **kwargs)
                embedding = NendoEmbedding(
                    track_id=track.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                embeddings.append(embedding)
            return embeddings

        return wrapper

    @staticmethod
    def run_track(
        func: Callable[[NendoPlugin, NendoTrack, Any], None],
    ) -> Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]:
        """Decorator to register a function to create a `NendoEmbedding` from a track.

        This decorator wraps the function and allows a plugin user to call the plugin with either a set of (signal, sr, text), a track or a collection.

        Args:
            func: Callable[[NendoPlugin, np.array, int, str, Any], None]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoEmbedding, List[NendoEmbedding]]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if isinstance(track_or_collection, NendoTrack):
                text, embedding_vector = func(self, track_or_collection, **kwargs)
                embedding = NendoEmbedding(
                    track_id=track_or_collection.id,
                    user_id=self.nendo_instance.library.user.id,
                    plugin_name=self.plugin_name,
                    plugin_version=self.plugin_version,
                    text=text,
                    embedding=embedding_vector,
                )
                try:
                    if self.config.replace_plugin_data is True:
                        existing_embeddings = (
                            self.nendo_instance.library.get_embeddings(
                                track_id=track_or_collection.id,
                                plugin_name=self.plugin_name,
                                plugin_version=self.plugin_version,
                            )
                        )
                        if len(existing_embeddings) > 0:
                            embedding_update = existing_embeddings[0]
                            embedding_update.text = text
                            embedding_update.embedding = embedding_vector
                            embedding = self.nendo_instance.library.update_embedding(
                                embedding_update,
                            )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                except AttributeError as e:  # noqa: F841
                    self.logger.error(
                        "Failed to save the embedding to the library. "
                        "Please use a library plugin with vector support to "
                        "enable automatic storing of embeddings.",
                    )
                return embedding
            if isinstance(track_or_collection, NendoCollection):
                embeddings = []
                for track in track_or_collection.tracks():
                    text, embedding_vector = func(self, track, **kwargs)
                    embedding = NendoEmbedding(
                        track_id=track.id,
                        user_id=self.nendo_instance.library.user.id,
                        plugin_name=self.plugin_name,
                        plugin_version=self.plugin_version,
                        text=text,
                        embedding=embedding_vector,
                    )
                    try:
                        if self.config.replace_plugin_data is True:
                            existing_embeddings = (
                                self.nendo_instance.library.get_embeddings(
                                    track_id=track_or_collection.id,
                                    plugin_name=self.plugin_name,
                                    plugin_version=self.plugin_version,
                                )
                            )
                            if len(existing_embeddings) > 0:
                                embedding_update = existing_embeddings[0]
                                embedding_update.text = text
                                embedding_update.embedding = embedding_vector
                                embedding = (
                                    self.nendo_instance.library.update_embedding(
                                        embedding_update,
                                    )
                                )
                            else:
                                embedding = self.nendo_instance.library.add_embedding(
                                    embedding=embedding,
                                )
                        else:
                            embedding = self.nendo_instance.library.add_embedding(
                                embedding=embedding,
                            )
                    except AttributeError as e:  # noqa: F841
                        self.logger.error(
                            "Failed to save the embedding to the library. "
                            "Please use a library plugin with vector support to "
                            "enable automatic storing of embeddings.",
                        )
                    embeddings.append(embedding)
                return embeddings
            signal = kwargs.get("signal", None)
            sr = kwargs.get("sr", None)
            text = kwargs.get("text", None)
            new_track = self.nendo_instance.library.add_track_from_signal(
                signal=signal if signal is not None else np.array([]),
                sr=sr if sr is not None else self.config.default_sr,
                meta={"text": text},
            )
            kwargs.pop("signal", None)
            kwargs.pop("sr", None)
            kwargs.pop("text", None)
            text, embedding_vector = func(self, track=new_track, **kwargs)
            embedding = NendoEmbedding(
                track_id=new_track.id,
                user_id=self.nendo_instance.library.user.id,
                plugin_name=self.plugin_name,
                plugin_version=self.plugin_version,
                text=text,
                embedding=embedding_vector,
            )
            try:
                if self.config.replace_plugin_data is True:
                    existing_embeddings = self.nendo_instance.library.get_embeddings(
                        track_id=track_or_collection.id,
                        plugin_name=self.plugin_name,
                        plugin_version=self.plugin_version,
                    )
                    if len(existing_embeddings) > 0:
                        embedding_update = existing_embeddings[0]
                        embedding_update.text = text
                        embedding_update.embedding = embedding_vector
                        embedding = self.nendo_instance.library.update_embedding(
                            embedding_update,
                        )
                    else:
                        embedding = self.nendo_instance.library.add_embedding(
                            embedding=embedding,
                        )
                else:
                    embedding = self.nendo_instance.library.add_embedding(
                        embedding=embedding,
                    )
            except AttributeError as e:  # noqa: F841
                self.logger.error(
                    "Failed to save the embedding to the library. "
                    "Please use a library plugin with vector support to "
                    "enable automatic storing of embeddings.",
                )
            return embedding

        return wrapper

    @staticmethod
    def run_collection(
        func: Callable[[NendoPlugin, NendoCollection, Any], None],
    ) -> Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]:
        """Decorator to register a function to create a `NendoEmbedding` from a collection.

        This decorator wraps the function and allows a plugin user to call the plugin with either a set of (signal, sr, text), a track or a collection.

        Args:
            func: Callable[[NendoPlugin, np.array, int, str, Any], None]: The function to register.

        Returns:
            Callable[[NendoPlugin, Any], Union[NendoEmbedding, List[NendoEmbedding]]]: The wrapped function.
        """

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[NendoEmbedding, List[NendoEmbedding]]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            # TODO we currently have no way of handling embeddings of collections,
            # so we just return the function value(s) directly
            if isinstance(track_or_collection, NendoCollection):
                return func(self, track_or_collection, **kwargs)
            if track_or_collection is None:
                signal = kwargs.get("signal", None)
                sr = kwargs.get("sr", None)
                text = kwargs.get("text", None)
                track_or_collection = self.nendo_instance.library.add_track_from_signal(
                    signal=signal if signal is not None else np.array([]),
                    sr=sr if sr is not None else self.config.default_sr,
                    meta={"text": text},
                )
                kwargs.pop("signal", None)
                kwargs.pop("sr", None)
                kwargs.pop("text", None)

            tmp_collection = self.nendo_instance.library.add_collection(
                name="tmp",
                track_ids=[track_or_collection.id],
                collection_type="temp",
            )
            return func(self, tmp_collection, **kwargs)

        return wrapper

    def __call__(
        self,
        **kwargs: Any,
    ) -> Optional[Union[NendoEmbedding, List[NendoEmbedding], [str, np.ndarray]]]:
        """Call the plugin.

        Runs a registered run function of a plugin on a text, a track, a collection.
        If the plugin has more than one run function, a warning is raised and all the possible options are listed.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Optional[
                Union[
                    NendoEmbedding,
                    List[NendoEmbedding],
                    [str, np.ndarray],
                    List[Tuple[str, np.ndarray]
                ],
            ]: The NendoEmbedding, if run on a track. A list of NendoEmbeddings,
            if run on a collection of tracks. The text and corresponding vector as numpy.ndarray,
            if run on a text.
        """
        wrapped_methods = get_wrapped_methods(self)
        if len(wrapped_methods) > 1:
            # if called with text run first method that can call text
            # which we assume is decorated with `@run_text`
            if "text" in kwargs:
                for wrapped_method in wrapped_methods:
                    if "text" in inspect.signature(wrapped_method).parameters:
                        return wrapped_method(self, **kwargs)

            elif "track" in kwargs or "collection" in kwargs:
                # remove @run_text function
                wrapped_methods = [
                    w
                    for w in wrapped_methods
                    if "text" not in inspect.signature(w).parameters
                ]

                if len(wrapped_methods) > 1:
                    self.logger.warning(
                        self._generate_multiple_wrapped_warning(wrapped_methods),
                    )
                    return None

        if len(wrapped_methods) == 0:
            raise NendoPluginRuntimeError(
                "No wrapped embedding plugin function found. "
                "Please implement at least a function with the "
                "`@run_text` wrapper.",
            )
        run_func = wrapped_methods[0]
        return run_func(self, **kwargs)


class NendoUtilityPlugin(NendoPlugin):
    """Basic class for nendo utility plugins."""

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "UtilityPlugin"

    @staticmethod
    def run_utility(
        func: Callable[
            [NendoPlugin, Optional[NendoTrack], Any],
            Union[str, float, int, bool, List],
        ],
    ) -> Callable[[NendoPlugin, Any], Union[str, float, int, bool, List]]:
        """Run utility plugin."""

        @functools.wraps(func)
        def wrapper(self, **kwargs: Any) -> Union[str, float, int, bool, List]:
            track_or_collection, kwargs = self._pop_track_or_collection_from_args(
                **kwargs,
            )
            if track_or_collection is None:
                return func(self, **kwargs)
            return func(self, track_or_collection, **kwargs)

        return wrapper


class NendoLibraryPlugin(NendoPlugin):
    """Basic class for nendo library plugins."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    storage_driver: Optional[NendoStorage] = None

    # ==========================
    #
    # TRACK MANAGEMENT FUNCTIONS
    #
    # ==========================

    @abstractmethod
    def add_track(
        self,
        file_path: Union[FilePath, str],
        track_type: str = "track",
        copy_to_library: Optional[bool] = None,
        skip_duplicate: Optional[bool] = None,
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Add the track given by path to the library.

        Args:
            file_path (Union[FilePath, str]): Path to the file to add as track.
            track_type (str): Type of the track. Defaults to "track".
            copy_to_library (bool, optional): Flag that specifies whether
                the file should be copied into the library directory.
                Defaults to None.
            skip_duplicate (bool, optional): Flag that specifies whether a
                file should be added that already exists in the library, based on its
                file checksum. Defaults to None.
            user_id (UUID, optional): ID of user adding the track.
            meta (dict, optional): Metadata to attach to the track upon adding.

        Returns:
            NendoTrack: The track that was added to the library.
        """
        raise NotImplementedError

    @abstractmethod
    def add_track_from_signal(
        self,
        signal: np.ndarray,
        sr: int,
        track_type: str = "track",
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Add a track to the library that is described by the given signal.

        Args:
            signal (np.ndarray): The numpy array containing the audio signal.
            sr (int): Sample rate
            track_type (str): Track type. Defaults to "track".
            user_id (UUID, optional): The ID of the user adding the track.
            meta (Dict[str, Any], optional): Track metadata. Defaults to {}.

        Returns:
            schema.NendoTrack: The added NendoTrack
        """
        raise NotImplementedError

    @abstractmethod
    def add_related_track(
        self,
        file_path: Union[FilePath, str],
        related_track_id: Union[str, uuid.UUID],
        track_type: str = "str",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_meta: Optional[Dict[str, Any]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Add track that is related to another `NendoTrack`.

        Add the track found in the given path to the library and create a relationship
        in the new track that points to the track identified by related_to.

        Args:
            file_path (Union[FilePath, str]): Path to the file to add as track.
            related_track_id (Union[str, uuid.UUID]): ID of the related track.
            track_type (str, optional): Track type. Defaults to "track".
            user_id (Union[str, UUID], optional): ID of the user adding the track.
            track_meta (dict, optional): Dictionary containing the track metadata.
            relationship_type (str, optional): Type of the relationship.
                Defaults to "relationship".
            meta (dict, optional): Dictionary containing metadata about
                the relationship. Defaults to None in which case it'll be set to {}.

        Returns:
            NendoTrack: The track that was added to the Library
        """
        raise NotImplementedError

    @abstractmethod
    def add_related_track_from_signal(
        self,
        signal: np.ndarray,
        sr: int,
        related_track_id: Union[str, uuid.UUID],
        track_type: str = "track",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_meta: Optional[Dict[str, Any]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Add signal as track that is related to another `NendoTrack`.

        Add the track represented by the provided signal to the library and create a
        relationship in the new track that points to the track passed as related_to.

        Args:
            signal (np.ndarray): Waveform of the track in numpy array form.
            sr (int): Sampling rate of the waveform.
            related_track_id (Union[str, uuid.UUID]): ID to which the relationship
                should point to.
            track_type (str, optional): Track type. Defaults to "track".
            user_id (Union[str, uuid.UUID], optional): ID of the user adding the track.
            track_meta  (dict, optional): Dictionary containing the track metadata.
            relationship_type (str, optional): Type of the relationship.
                Defaults to "relationship".
            meta (dict, optional): Dictionary containing metadata about
                the relationship. Defaults to None in which case it'll be set to {}.

        Returns:
            NendoTrack: The added track with the relationship.
        """
        raise NotImplementedError

    @abstractmethod
    def add_tracks(
        self,
        path: Union[str, DirectoryPath],
        track_type: str = "track",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        copy_to_library: Optional[bool] = None,
        skip_duplicate: bool = True,
    ) -> NendoCollection:
        """Scan the provided path and upsert the information into the library.

        Args:
            path (Union[DirectoryPath, str]): Path to the directory to scan.
            track_type (str): Track type. Defaults to "track".
            user_id (UUID, optional): The ID of the user adding the tracks.
            copy_to_library (bool, optional): Flag that specifies whether
                the file should be copied into the library directory.
                Defaults to None.
            skip_duplicate (bool, optional): Flag that specifies whether a
                file should be added that already exists in the library, based on its
                file checksum. Defaults to None.

        Returns:
            collection (NendoCollection): The collection of tracks that were added to the Library
        """
        raise NotImplementedError

    @abstractmethod
    def update_track(
        self,
        track: NendoTrack,
    ) -> NendoTrack:
        """Updates the given collection by storing it to the database.

        Args:
            track (NendoTrack): The track to be stored to the database.

        Raises:
            NendoTrackNotFoundError: If the track passed to the function
                does not exist in the database.

        Returns:
            NendoTrack: The updated track.
        """
        raise NotImplementedError

    @abstractmethod
    def add_plugin_data(
        self,
        track_id: Union[str, uuid.UUID],
        key: str,
        value: Any,
        plugin_name: str,
        plugin_version: Optional[str] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        replace: Optional[bool] = None,
    ) -> NendoPluginData:
        """Add plugin data to a NendoTrack and persist changes into the DB.

        Args:
            track_id (Union[str, uuid.UUID]): ID of the track to which
                the plugin data should be added.
            key (str): Key under which to save the data.
            value (str): Data to  save.
            plugin_name (str): Name of the plugin.
            plugin_version (str, optional): Version of the plugin. Defaults to None
                in which case the version will be inferred from the currently
                registered version of the plugin.
            user_id (Union[str, uuid.UUID], optional): ID of user adding the
                plugin data.
            replace (bool, optional): Flag that determines whether
                the last existing data point for the given plugin name and -version
                is overwritten or not. Defaults to False.

        Returns:
            NendoPluginData: The saved plugin data as a NendoPluginData object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_track(
        self,
        track_id: uuid.UUID,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> NendoTrack:
        """Get a single track from the library by ID.

        If no track with the given ID was found, return None.

        Args:
            track_id (Any): The ID of the track to get.
            user_id (uuid4, optional): ID of user adding the plugin data.

        Returns:
            track (NendoTrack): The track with the given ID
        """
        raise NotImplementedError

    @abstractmethod
    @NendoPlugin.stream_output
    def get_tracks(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        load_related_tracks: bool = False,
    ) -> Union[List, Iterator]:
        """Get tracks based on the given query parameters.

        Args:
            user_id (Union[str, UUID], optional): ID of user getting the tracks.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results
                ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).
            load_related_tracks (bool, optional): Flag to control whether the
                `related_tracks` will be populated or not. Defaults to False.

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def get_related_tracks(
        self,
        track_id: Union[str, uuid.UUID],
        direction: str = "to",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Get tracks with a relationship to the track with track_id.

        Args:
            track_id (str): ID of the track to be searched for.
            direction (str, optional): The relationship direction
                Can be either one of "to", "from", or "both". Defaults to "to".
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def filter_related_tracks(
        self,
        track_id: Union[str, uuid.UUID],
        direction: str = "to",
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[Dict[str, Any]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Get tracks with a relationship to a track and filter the results.

        Args:
            track_id (Union[str, UUID]): ID of the track to be searched for.
            direction (str, optional): The relationship direction
                Can be either one of "to", "from", or "both". Defaults to "to".
            filters (dict, optional): Dictionary containing the filters to apply.
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
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def find_tracks(
        self,
        value: str,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Find tracks by searching for a string through the resource metadata.

        Args:
            value (str): The search value to filter by.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Name of the field by which to order.
                Defaults to None in which case no specific ordering will be applied.
            order (str, optional): Ordering direction. Defaults to "asc".
            limit (str, optional): Pagination limit.
            offset (str, optional): Pagination offset.

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def filter_tracks(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[Dict[str, Any]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Obtain tracks from the db by filtering over plugin data.

        Args:
            filters (dict, optional): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict): Dictionary containing the keywords to search for
                over the track.resource.meta field. The dictionary's values
                should contain singular search tokens and  the keys currently have no
                effect but might in the future. Defaults to {}.
            track_type (Union[str, List[str]], optional): Track type to filter for.
                Can be a singular type or a list of types. Defaults to None.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            collection_id (Union[str, uuid.UUID], optional): Collection id to
                which the filtered tracks must have a relationship. Defaults to None.
            plugin_names (list, optional): List used for applying the filter only to
                data of certain plugins. If None, all plugin data related to the track
                is used for filtering.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Ordering ("asc" vs "desc"). Defaults to "asc".
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def remove_track(
        self,
        track_id: Union[str, uuid.UUID],
        user_id: Optional[Union[str, uuid.UUID]] = None,
        remove_relationships: bool = False,
        remove_plugin_data: bool = True,
        remove_resources: bool = True,
    ) -> bool:
        """Delete track from library by ID.

        Args:
            track_id (Union[str, uuid.UUID]): The ID of the track to remove.
            user_id (Union[str, UUID], optional): The ID of the user
                owning the track.
            remove_relationships (bool):
                If False prevent deletion if related tracks exist,
                if True delete relationships together with the object.
                Defaults to False.
            remove_plugin_data (bool):
                If False prevent deletion if related plugin data exist,
                if True delete plugin data together with the object.
                Defaults to True.
            remove_resources (bool):
                If False, keep the related resources, e.g. files,
                if True, delete the related resources.
                Defaults to True.

        Returns:
            success (bool): True if removal was successful, False otherwise
        """
        raise NotImplementedError

    def export_track(
        self,
        track_id: Union[str, uuid.UUID],
        file_path: str,
        file_format: str = "wav",
    ) -> str:
        """Export the track to a file.

        Args:
            track_id (Union[str, uuid.UUID]): The ID of the target track to export.
            file_path (str): Path to the exported file. Can be either a full
                file path or a directory path. If a directory path is given,
                a filename will be automatically generated and the file will be
                exported to the format specified as file_format. If a full file
                path is given, the format will be deduced from the path and the
                file_format parameter will be ignored.
            file_format (str, optional): Format of the exported track. Ignored if
                file_path is a full file path. Defaults to "wav".

        Returns:
            str: The path to the exported file.
        """
        raise NotImplementedError

    # ===============================
    #
    # COLLECTION MANAGEMENT FUNCTIONS
    #
    # ===============================

    @abstractmethod
    def add_collection(
        self,
        name: str,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        description: str = "",
        collection_type: str = "collection",
        visibility: Visibility = Visibility.private,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Creates a new collection and saves it into the DB.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids
                to be added to the collection.
            name (str): Name of the collection.
            user_id (UUID, optional): The ID of the user adding the collection.
            description (str): Description of the collection.
            collection_type (str): Type of the collection. Defaults to "collection".
            visibility (str, optional): Visibility of the track in multi-user settings.
                Defaults to "private".
            meta (Dict[str, Any]): Metadata of the collection.

        Returns:
            schema.NendoCollection: The newly created NendoCollection object.
        """
        raise NotImplementedError

    @abstractmethod
    def add_related_collection(
        self,
        track_ids: List[Union[str, uuid.UUID]],
        collection_id: Union[str, uuid.UUID],
        name: str,
        description: str = "",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Add a collection that is related to another `NendoCollection`.

        Add a new collection with a relationship to and from the collection
        with the given collection_id.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids.
            collection_id (Union[str, uuid.UUID]): Existing collection id.
            name (str): Name of the new related collection.
            description (str): Description of the new related collection.
            user_id (UUID, optional): The ID of the user adding the collection.
            relationship_type (str): Type of the relationship.
            meta (Dict[str, Any]): Meta of the new related collection.

        Returns:
            schema.NendoCollection: The newly added NendoCollection object.
        """
        raise NotImplementedError

    @abstractmethod
    def add_track_to_collection(
        self,
        track_id: Union[str, uuid.UUID],
        collection_id: Union[str, uuid.UUID],
        position: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Creates a relationship from the track to the collection.

        Args:
            collection_id (Union[str, uuid.UUID]): Collection id.
            track_id (Union[str, uuid.UUID]): Track id.

        Returns:
            schema.NendoCollection: The updated NendoCollection object.
        """
        raise NotImplementedError

    @abstractmethod
    def add_tracks_to_collection(
        self,
        track_ids: List[Union[str, uuid.UUID]],
        collection_id: Union[str, uuid.UUID],
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Creates a relationship from the track to the collection.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids to add.
            collection_id (Union[str, uuid.UUID]): ID of the collection to
                which to add the track.
            meta (Dict[str, Any], optional): Metadata of the relationship.

        Returns:
            NendoCollection: The updated NendoCollection object.
        """
        return NotImplementedError

    @abstractmethod
    def get_collection_tracks(
        self,
        collection_id: uuid.UUID,
        order: Optional[str] = "asc",
    ) -> List[NendoTrack]:
        """Get all tracks of a collection.

        Args:
            collection_id (Union[str, uuid.UUID]): ID of the collection from which to
                get all tracks.
            order (str, optional): Ordering direction. Defaults to "asc".

        Returns:
            List[NendoTrack]: List of tracks in the collection.
        """
        raise NotImplementedError

    @abstractmethod
    def get_collection(
        self,
        collection_id: uuid.uuid4,
        get_related_tracks: bool = True,
    ) -> NendoCollection:
        """Get a collection by its ID.

        Args:
            collection_id (uuid.uuid4): ID of the target collection.
            get_related_tracks (bool, optional): Flag that defines whether the
                returned collection should contain the `related_tracks`.
                Defaults to True.

        Returns:
            NendoCollection: The collection object.
        """
        raise NotImplementedError

    @abstractmethod
    @NendoPlugin.stream_output
    def get_collections(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Get a list of collections.

        Args:
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results
                ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of collections, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def find_collections(
        self,
        value: str = "",
        collection_types: Optional[List[str]] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Find collections with a search term in the description or meta field.

        Args:
            value (str): Term to be searched for in the description and meta field.
            collection_types (List[str], optional): Collection types to filter for.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of collections, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def get_related_collections(
        self,
        collection_id: Union[str, uuid.UUID],
        direction: str = "to",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Get collections with a relationship to the collection with collection_id.

        Args:
            collection_id (str): ID of the collection to be searched for.
            direction (str, optional): The relationship direction
                Can be either one of "to", "from", or "both". Defaults to "to".
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of collections, depending on the
                configuration variable stream_mode
        """
        raise NotImplementedError

    @abstractmethod
    def update_collection(
        self,
        collection: NendoCollection,
    ) -> NendoCollection:
        """Updates the given collection by storing it to the database.

        Args:
            collection (NendoCollection): The collection to store.

        Raises:
            NendoCollectionNotFoundError: If the collection with
                the given ID was not found.

        Returns:
            NendoCollection: The updated collection.
        """
        raise NotImplementedError

    @abstractmethod
    def collection_size(
        self,
        collection_id: Union[str, uuid.UUID],
    ) -> int:
        """Get the number of tracks in a collection.

        Args:
            collection_id (Union[str, uuid.UUID]): The ID of the collection.

        Returns:
            int: The number of tracks.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_track_from_collection(
        self,
        track_id: Union[str, uuid.UUID],
        collection_id: Union[str, uuid.UUID],
    ) -> bool:
        """Deletes a relationship from the track to the collection.

        Args:
            collection_id (Union[str, uuid.UUID]): Collection id.
            track_id (Union[str, uuid.UUID]): Track id.

        Returns:
            success (bool): True if removal was successful, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_collection(
        self,
        collection_id: uuid.UUID,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        remove_relationships: bool = False,
    ) -> bool:
        """Deletes the collection identified by `collection_id`.

        Args:
            collection_id (uuid.UUID): ID of the collection to remove.
            user_id (Union[str, UUID], optional): The ID of the user.
            remove_relationships (bool, optional):
                If False prevent deletion if related tracks exist,
                if True delete relationships together with the object.
                Defaults to False.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        raise NotImplementedError

    def export_collection(
        self,
        collection_id: Union[str, uuid.UUID],
        export_path: str,
        filename_suffix: str = "_nendo",
        file_format: str = "wav",
    ) -> List[str]:
        """Export the track to a file.

        Args:
            collection_id (Union[str, uuid.UUID]): The ID of the target
                collection to export.
            export_path (str): Path to a directory into which the collection's tracks
                should be exported.
            filename_suffix (str): The suffix which should be appended to each
                exported track's filename.
            file_format (str, optional): Format of the exported track. Ignored if
                file_path is a full file path. Defaults to "wav".

        Returns:
            List[str]: A list with all full paths to the exported files.
        """
        raise NotImplementedError

    # =========================
    #
    # BLOB MANAGEMENT FUNCTIONS
    #
    # =========================

    @abstractmethod
    def store_blob(
        self,
        file_path: Union[FilePath, str],
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> NendoBlob:
        """Stores a blob of data.

        Args:
            file_path (Union[FilePath, str]): Path to the file to store as blob.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's storing the file to blob.

        Returns:
            schema.NendoBlob: The stored blob.
        """
        raise NotImplementedError

    @abstractmethod
    def store_blob_from_bytes(
        self,
        data: bytes,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> NendoBlob:
        """Stores a data of type `bytes` to a blob.

        Args:
            data (bytes): The blob to store.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's storing the bytes to blob.

        Returns:
            schema.NendoBlob: The stored blob.
        """
        raise NotImplementedError

    @abstractmethod
    def load_blob(
        self,
        blob_id: uuid.UUID,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> NendoBlob:
        """Loads a blob of data into memory.

        Args:
            blob_id (uuid.UUID): The UUID of the blob.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's loading the blob.

        Returns:
            schema.NendoBlob: The loaded blob.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_blob(
        self,
        blob_id: uuid.UUID,
        remove_resources: bool = True,
        user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Deletes a blob of data.

        Args:
            blob_id (uuid.UUID): The UUID of the blob.
            remove_resources (bool): If True, remove associated resources.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's removing the blob.

        Returns:
            success (bool): True if removal was successful, False otherwise
        """
        raise NotImplementedError

    # ==================================
    #
    # MISCELLANEOUS MANAGEMENT FUNCTIONS
    #
    # ==================================

    def __len__(self):
        """Obtain the number of tracks."""
        return self.library_size()

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError

    @abstractmethod
    def library_size(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> int:
        """Get the number of all tracks in the library (per user).

        Args:
            user_id (Union[str, uuid.UUID], optional): The ID of the user.
                If not specified, the number of all tracks across all users is
                returned. Defaults to None.

        Returns:
            int: The number of tracks.
        """
        raise NotImplementedError

    def get_track_or_collection(
        self,
        target_id: Union[str, uuid.UUID],
    ) -> Union[NendoTrack, NendoCollection]:
        """Return a track or a collection based on the given target_id.

        Args:
            target_id (Union[str, uuid.UUID]): The target ID to obtain.

        Returns:
            Union[NendoTrack, NendoCollection]: The track or the collection.
        """
        target_id = ensure_uuid(target_id)
        collection = self.get_collection(target_id)
        if collection is not None:
            return collection

        # assume the id is a track id
        return self.get_track(target_id)

    def verify(self, action: Optional[str] = None, user_id: str = "") -> None:
        """Verify the library's integrity.

        Args:
            action (str, optional): Default action to choose when an
                inconsistency is detected. Choose between (i)gnore and (r)emove.
        """
        original_config = {}
        try:
            original_config["stream_mode"] = self.config.stream_mode
            original_config["stream_chunk_size"] = self.config.stream_chunk_size
            self.config.stream_mode = False
            self.config.stream_chunk_size = 16
            for track in self.get_tracks():
                if not self.storage_driver.file_exists(
                    file_name=track.resource.file_name,
                    user_id=user_id,
                ):
                    action = (
                        action
                        or input(
                            f"Inconsistency detected: {track.resource.src} "
                            "does not exist. Please choose an action:\n"
                            "(i) ignore - (r) remove",
                        ).lower()
                    )
                    if action == "i":
                        self.logger.warning(
                            "Detected missing file "
                            f"{track.resource.src} but instructed "
                            "to ignore.",
                        )
                        continue
                    if action == "r":
                        self.logger.info(
                            f"Removing track with ID {track.id} "
                            f"due to missing file {track.resource.src}",
                        )
                        self.remove_track(
                            track_id=track.id,
                            remove_plugin_data=True,
                            remove_relationships=True,
                            remove_resources=False,
                        )
            for library_file in self.storage_driver.list_files(user_id=user_id):
                file_without_ext = os.path.splitext(library_file)[0]
                if len(self.find_tracks(value=file_without_ext)) == 0:
                    action = (
                        action
                        or input(
                            f"Inconsistency detected: File {library_file} "
                            "cannot be fonud in database. Please choose an action:\n"
                            "(i) ignore - (r) remove",
                        ).lower()
                    )
                    if action == "i":
                        self.logger.warning(
                            f"Detected orphaned file {library_file} "
                            f"but instructed to ignore.",
                        )
                        continue
                    if action == "r":
                        self.logger.info(f"Removing orphaned file {library_file}")
                        self.storage_driver.remove_file(
                            file_name=library_file,
                            user_id=user_id,
                        )

        finally:
            self.config.stream_mode = original_config["stream_mode"]
            self.config.stream_chunk_size = original_config["stream_chunk_size"]

    @abstractmethod
    def reset(
        self,
        force: bool = False,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> None:
        """Reset the nendo library.

        Erase all tracks, collections and relationships.
        Ask before erasing.

        Args:
            force (bool, optional): Flag that specifies whether to ask the user for
                confirmation of the operation. Default is to ask the user.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's resetting the library. If none is given, the configured
                nendo default user will be used.
        """
        raise NotImplementedError

    def __str__(self):
        output = f"{self.plugin_name}, version {self.plugin_version}:\n"
        output += f"{len(self)} tracks"
        return output

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "LibraryPlugin"
