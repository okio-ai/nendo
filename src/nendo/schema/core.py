# -*- encoding: utf-8 -*-
# ruff: noqa: A003, TCH002, TCH001
"""Core schema definitions.

Contains class definitions for all common nendo objects.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
import pickle
import re
import shutil
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import librosa
import numpy as np
import soundfile as sf
from pydantic import BaseModel, ConfigDict, Field, FilePath

from nendo.config import NendoConfig
from nendo.main import Nendo
from nendo.schema.exception import NendoError, NendoPluginRuntimeError
from nendo.utils import (
    ensure_uuid,
    get_wrapped_methods,
    md5sum,
    play_signal,
    pretty_print,
)

logger = logging.getLogger("nendo")


class ResourceType(str, Enum):
    """Enum representing different types of resources used in Nendo."""

    audio: str = "audio"
    image: str = "image"
    model: str = "model"
    blob: str = "blob"


class ResourceLocation(str, Enum):
    """Enum representing differnt types of resource locations.

    (e.g. original filepath, local FS library path, S3 bucket, etc.)
    """

    original: str = "original"
    local: str = "local"
    gcs: str = "gcs"
    s3: str = "s3"


class Visibility(str, Enum):
    """Enum representing different visibilities of information in the nendo Library.

    Mostly relevant when sharing a nendo library between different users.
    """

    public: str = "public"
    private: str = "private"
    deleted: str = "deleted"


class NendoUserBase(BaseModel):  # noqa: D101
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        use_enum_values=True,
    )

    name: str
    password: str
    email: str
    avatar: str = "/assets/images/default_avatar.png"
    verified: bool = False
    last_login: datetime = Field(default_factory=datetime.now)


class NendoUser(NendoUserBase):
    """Basic class representing a Nendo user."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)


class NendoUserCreate(NendoUserBase):  # noqa: D101
    pass


class NendoTrackSlim(BaseModel):  # noqa: D101
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )

    id: uuid.UUID
    user_id: uuid.UUID
    track_type: str = "track"
    meta: Dict[str, Any] = Field(default_factory=dict)


class NendoCollectionSlim(BaseModel):  # noqa: D101
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )

    id: uuid.UUID
    name: str
    description: str = ""
    collection_type: str = "collection"
    user_id: uuid.UUID
    meta: Dict[str, Any] = Field(default_factory=dict)


class NendoResource(BaseModel, ABC):
    """Basic class representing a resource in Nendo.

    For example, every `NendoTrack` has at least one associated `NendoResource`,
    namely the file containing its waveform. But it can also have other associated
    resources in the form of images, etc.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    file_path: str
    file_name: str
    resource_type: ResourceType = ResourceType.audio
    location: ResourceLocation = ResourceLocation.local
    meta: Dict[str, Any] = Field(default_factory=dict)

    @property
    def src(self):  # noqa: D102
        return os.path.join(self.file_path, self.file_name)


class NendoRelationshipBase(BaseModel, ABC):
    """Base class representing a relationship between two Nendo Core objects."""

    model_config = ConfigDict(use_enum_values=True)

    source_id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    relationship_type: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class NendoRelationship(NendoRelationshipBase):
    """Base class for Nendo Core relationships.

    All relationship classes representing relationships between specific
    types of Nendo Core objects inherit from this class.
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )

    id: uuid.UUID


class NendoTrackTrackRelationship(NendoRelationship):
    """Class representing a relationship between two `NendoTrack`s."""

    source: NendoTrackSlim
    target: NendoTrackSlim


class NendoTrackCollectionRelationship(NendoRelationship):
    """Class representing a relationship between a `NendoTrack` and a `NendoCollection`."""

    source: NendoTrackSlim
    target: NendoCollectionSlim
    relationship_position: int


class NendoCollectionCollectionRelationship(NendoRelationship):
    """Class representing a relationship between two `NendoCollection`s."""

    source: NendoCollectionSlim
    target: NendoCollectionSlim


class NendoRelationshipCreate(NendoRelationshipBase):  # noqa: D101
    pass


class NendoPluginDataBase(BaseModel, ABC):  # noqa: D101
    model_config = ConfigDict(
        from_attributes=True,
    )

    track_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    plugin_name: str
    plugin_version: str
    key: str
    value: str


class NendoPluginData(NendoPluginDataBase):
    """Class representing basic plugin data attached to a track."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        # output = f"id: {self.id}"
        output = "----------------"
        output += f"\nplugin name: {self.plugin_name}"
        output += f"\nplugin version: {self.plugin_version}"
        # output += f"\nuser id: {self.user_id}"
        output += f"\nkey: {self.key}"
        output += f"\nvalue: {self.value}"
        return output


class NendoPluginDataCreate(NendoPluginDataBase):  # noqa: D101
    pass


class NendoTrackBase(BaseModel):
    """Base class for tracks in Nendo."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        use_enum_values=True,
    )

    nendo_instance: Optional[Nendo] = None
    user_id: uuid.UUID
    track_type: str = "track"
    visibility: Visibility = Visibility.private
    images: List[NendoResource] = Field(default_factory=list)
    resource: NendoResource
    related_tracks: List[NendoTrackTrackRelationship] = Field(default_factory=list)
    related_collections: List[NendoTrackCollectionRelationship] = Field(
        default_factory=list,
    )
    meta: Dict[str, Any] = Field(default_factory=dict)
    plugin_data: List[NendoPluginData] = Field(default_factory=list)

    def __init__(self, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(**kwargs)
        self.nendo_instance = Nendo()

    @property
    def signal(self) -> np.ndarray:
        """Lazy-load the signal from the track using librosa.

        Returns:
            np.ndarray: The signal of the track.
        """
        signal = self.__dict__.get("signal")
        if signal is None:
            track_local = self.nendo_instance.library.storage_driver.as_local(
                file_path=self.resource.src,
                location=self.resource.location,
                user_id=self.nendo_instance.config.user_id,
            )
            signal, sr = librosa.load(track_local, sr=self.sr, mono=False)
            self.__dict__["sr"] = sr
            self.__dict__["signal"] = signal
        return signal

    @property
    def sr(self) -> int:
        """Lazy-load the sample rate of the track.

        Returns:
            int: The sample rate of the track.
        """
        sr = self.__dict__.get("sr") or self.get_meta("sr")
        if sr is None:
            track_local = self.nendo_instance.library.storage_driver.as_local(
                file_path=self.resource.src,
                location=self.resource.location,
                user_id=self.nendo_instance.config.user_id,
            )
            sr = librosa.get_samplerate(track_local)
            self.set_meta({"sr": sr})
            self.__dict__["sr"] = sr
        return sr

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # noqa: D102
        result = super().model_dump(*args, **kwargs)
        # remove properties
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, property):
                result.pop(name, None)
        return result

    def __getitem__(self, key: str) -> Any:
        return self.meta[key]


class NendoTrack(NendoTrackBase):
    """Basic class representing a nendo track."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        output = f"\nid: {self.id}"
        output += f"\nsample rate: {self.sr}"
        output += f"{pretty_print(self.meta)}"
        return output

    def __len__(self):
        """Return the length of the track in seconds."""
        return self.signal.shape[1] / self.sr

    @classmethod
    def model_validate(cls, *args, **kwargs):
        """Inject the nendo instance upon conversion from ORM."""
        instance = super().model_validate(*args, **kwargs)
        instance.nendo_instance = Nendo()
        return instance

    def resample(self, rsr: int = 44100) -> np.ndarray:
        """Resample track."""
        new_signal = librosa.resample(self.signal, orig_sr=self.sr, target_sr=rsr)
        self.__dict__["signal"] = new_signal
        self.__dict__["sr"] = rsr
        return new_signal

    def local(self) -> str:
        """Get a path to a local file handle on the track."""
        return self.nendo_instance.library.storage_driver.as_local(
            file_path=self.resource.src,
            location=self.resource.location,
            user_id=self.nendo_instance.config.user_id,
        )

    def overlay(self, track: NendoTrack, gain_db: Optional[float] = 0) -> NendoTrack:
        """Overlay two tracks using gain control in decibels.

        The gain gets applied to the second track.
        This function creates a new related track in the library.

        Args:
            track (NendoTrack): The track to overlay with.
            gain_db (Optional[float], optional): The gain to apply to the second track.
                Defaults to 0.

        Returns:
            NendoTrack: The resulting mixed track.
        """
        if self.sr > track.sr:
            self.resample(track.sr)
        elif self.sr < track.sr:
            track.resample(self.sr)

        if self.signal.shape[1] > track.signal.shape[1]:
            signal_one = self.signal[:, : track.signal.shape[1]]
            signal_two = track.signal
        else:
            signal_one = self.signal
            signal_two = track.signal[:, : self.signal.shape[1]]

        # Convert dB gain to linear gain factor
        gain_factor_during_overlay = 10 ** (gain_db / 20)

        new_signal = signal_one + (signal_two * gain_factor_during_overlay)
        return self.nendo_instance.library.add_related_track_from_signal(
            signal=new_signal,
            sr=self.sr,
            track_type="track",
            related_track_id=self.id,
            track_meta={"overlay_parameters": {"gain_db": gain_db}},
        )

    def slice(self, end: float, start: Optional[float] = 0) -> np.ndarray:
        """Slice a track.

        Args:
            end (float): End of the slice in seconds.
            start (Optional[float], optional): Start of the slice in seconds.
                Defaults to 0.

        Returns:
            np.ndarray: The sliced track.
        """
        start_frame = int(start * self.sr)
        end_frame = int(end * self.sr)
        return self.signal[:, start_frame:end_frame]

    def save(self) -> NendoTrack:
        """Save the track to the library.

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.update_track(track=self)
        return self

    def delete(
        self,
        remove_relationships: bool = False,
        remove_plugin_data: bool = True,
        remove_resources: bool = True,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> NendoTrack:
        """Delete the track from the library.

        Args:
            remove_relationships (bool):
                If False prevent deletion if related tracks exist,
                if True delete relationships together with the object
            remove_plugin_data (bool):
                If False prevent deletion if related plugin data exist
                if True delete plugin data together with the object
            remove_resources (bool):
                If False, keep the related resources, e.g. files
                if True, delete the related resources
            user_id (Union[str, UUID], optional): The ID of the user owning the track.

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.remove_track(
            track_id=self.id,
            remove_relationships=remove_relationships,
            remove_plugin_data=remove_plugin_data,
            remove_resources=remove_resources,
            user_id=user_id,
        )
        return self

    def set_meta(self, meta: Dict[str, Any]) -> NendoTrack:
        """Set metadata of track.

        Args:
            meta (Dict[str, Any]): Dictionary containing the metadata to be set.

        Returns:
            NendoTrack: The track itself.
        """
        try:
            self.meta.update(meta)
            self.nendo_instance.library.update_track(track=self)
        except NendoError as e:
            logger.exception("Error updating meta: %s", e)
        return self

    def has_meta(self, key: str) -> bool:
        """Check if a given track has the given key in its meta dict.

        Args:
            key (str): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return any(k == key for k in self.meta)

    def get_meta(self, key: str) -> Dict[str, Any]:
        """Get the meta entry for the given key.

        Args:
            key (str): The key to get metadata for.

        Returns:
            Dict[str, Any]: Meta entry for given key.
        """
        if not self.has_meta(key):
            logger.error("Key not found in meta: %s", key)
            return None
        return self.meta[key]

    def remove_meta(self, key: str) -> NendoTrack:
        """Remove the meta entry for the given key.

        Args:
            key (str): The key to remove metadata for.

        Returns:
            NendoTrack: The track itself.
        """
        if not self.has_meta(key):
            logger.error("Key not found in meta: %s", key)
            return None
        _ = self.meta.pop(key, None)
        self.nendo_instance.library.update_track(track=self)
        return self

    def add_plugin_data(
        self,
        plugin_name: str,
        plugin_version: str,
        key: str,
        value: str,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        replace: bool = True,
    ) -> NendoTrack:
        """Add plugin data to a NendoTrack and persist changes into the DB.

        Args:
            plugin_name (str): Name of the plugin.
            plugin_version (str): Version of the plugin.
            key (str): Key under which to save the data.
            value (Any): Data to save.
            user_id (Union[str, UUID], optional): ID of user adding the plugin data.
            replace (bool, optional): Flag that determines whether
                the last existing data point for the given plugin name and -version
                is overwritten or not. Defaults to True.

        Returns:
            NendoTrack: The track itself.
        """
        pd = self.nendo_instance.library.add_plugin_data(
            track_id=self.id,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            key=key,
            value=value,
            user_id=user_id,
            replace=replace,
        )
        self.plugin_data.append(pd)
        return self

    def get_plugin_data(
        self,
        plugin_name: str = "",
        key: str = "",
    ) -> Union[List[NendoPluginData], str, NendoBlob]:
        """Get all plugin data related to the given plugin name and the given key.

        Note: Function behavior
            - If no plugin_name is specified, all plugin data found with the given
                key is returned.
            - If no key is specified, all plugin data found with the given
                plugin_name is returned.
            - If neither key, nor plugin_name is specified, all plugin data
                is returned.
            - If the return value is a single item, it's `value` will be returned
                directly, otherwise a list of `NendoPluginData` will be returned.
            - Certain kinds of plugin data are actually stored as blobs
                and the corresponding blob id is stored in the plugin data's value
                field. Those will be automatically loaded from the blob into memory
                and a `NendoBlob` object will be returned inside `plugin_data.value`.

        Args:
            plugin_name (str): The name of the plugin to get the data for.
                Defaults to "".
            key (str): The key to filter plugin data for.
                Defaults to "".

        Returns:
            List[NendoPluginData]: List of nendo plugin data entries.
        """
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
            r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z",
            re.I,
        )
        plugin_data = []
        for pd in self.plugin_data:
            if (pd.plugin_name == plugin_name or len(plugin_name) == 0) and (
                pd.key == key or len(key) == 0
            ):
                # if we have a UUID, load the corresponding blob
                if uuid_pattern.match(pd.value):
                    pd_loaded = self.nendo_instance.library.load_blob(
                        blob_id=uuid.UUID(pd.value),
                    )
                    plugin_data.append(pd_loaded)
                # otherwise it's "normal" (non-blobified) data, load directly
                else:
                    plugin_data.append(pd)
        if len(plugin_data) == 1:
            return plugin_data[0].value
        return plugin_data

    def add_related_track(
        self,
        file_path: FilePath,
        track_type: str = "str",
        user_id: Optional[uuid.UUID] = None,
        track_meta: Optional[Dict[str, Any]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Adds a new track with a relationship to the current one.

        Args:
            file_path (FilePath): Path to the file to add as track.
            track_type (str): Track type. Defaults to "track".
            user_id (Union[str, UUID], optional): ID of the user adding the track.
            track_meta (dict, optional): Dictionary containing the track metadata.
            relationship_type (str): Type of the relationship.
                Defaults to "relationship".
            meta (dict): Dictionary containing metadata about
                the relationship. Defaults to {}.

        Returns:
            NendoTrack: The track itself.
        """
        related_track = self.nendo_instance.library.add_related_track(
            file_path=file_path,
            related_track_id=self.id,
            track_type=track_type,
            user_id=user_id or self.user_id,
            track_meta=track_meta,
            relationship_type=relationship_type,
            meta=meta,
        )
        self.related_tracks.append(related_track.related_tracks[0])
        return self

    def add_related_track_from_signal(
        self,
        signal: np.ndarray,
        sr: int,
        track_type: str = "track",
        user_id: Optional[uuid.UUID] = None,
        track_meta: Optional[Dict[str, Any]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Adds a new track with a relationship to the current one.

        Args:
            signal (np.ndarray): Waveform of the track in numpy array form.
            sr (int): Sampling rate of the waveform.
            track_type (str): Track type. Defaults to "track".
            user_id (UUID, optional): ID of the user adding the track.
            track_meta  (dict, optional): Dictionary containing the track metadata.
            relationship_type (str): Type of the relationship.
                Defaults to "relationship".
            meta (dict): Dictionary containing metadata about
                the relationship. Defaults to {}.

        Returns:
            NendoTrack: The track itself.
        """
        related_track = self.nendo_instance.library.add_related_track_from_signal(
            signal=signal,
            sr=sr,
            track_type=track_type,
            related_track_id=self.id,
            user_id=user_id,
            track_meta=track_meta,
            relationship_type=relationship_type,
            meta=meta,
        )
        self.related_tracks.append(related_track.related_tracks[0])
        return self

    def has_relationship(self, relationship_type: str = "relationship") -> bool:
        """Check whether the track has any relationships of the specified type.

        Args:
            relationship_type (str): Type of the relationship to check for.
                Defaults to "relationship".

        Returns:
            bool: True if a relationship of the given type exists, False otherwise.
        """
        all_relationships = self.related_tracks + self.related_collections
        if len(all_relationships) == 0:
            return False
        return any(r.relationship_type == relationship_type for r in all_relationships)

    def has_relationship_to(self, track_id: Union[str, uuid.UUID]) -> bool:
        """Check if the track has a relationship to the track with the given track_id.

        Args:
            track_id (Union[str, uuid.UUID]): ID of the track to which to check
                for relationships.

        Returns:
            bool: True if a relationship to the track with the given track_id exists.
                False otherwise.
        """
        track_id = ensure_uuid(track_id)
        if self.related_tracks is None:
            return False
        return any(r.target_id == track_id for r in self.related_tracks)

    def get_related_tracks(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[NendoTrack]:
        """Get all tracks to which the current track has a relationship.

        Args:
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (Optional[str]): Key used for ordering the results.
            order (Optional[str]): Order in which to retrieve results ("asc" or "desc").
            limit (Optional[int]): Limit the number of returned results.
            offset (Optional[int]): Offset into the paginated results (requires limit).

        Returns:
            List[NendoTrack]: List containting all related NendoTracks
        """
        return self.nendo_instance.library.get_related_tracks(
            track_id=self.id,
            user_id=user_id,
            order_by=order_by,
            order=order,
            limit=limit,
            offset=offset,
        )

    def add_to_collection(
        self,
        collection_id: Union[str, uuid.UUID],
        position: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoTrack:
        """Adds the track to the collection given as collection_id.

        Args:
            collection_id (Union[str, uuid.UUID]): ID of the collection to
                which to add the track.
            position (int, optional): Target position of the track inside
                the collection.
            meta (Dict[str, Any]): Metadata of the relationship.

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.add_track_to_collection(
            track_id=self.id,
            collection_id=collection_id,
            position=position,
            meta=meta,
        )
        return self

    def remove_from_collection(
        self,
        collection_id: Union[str, uuid.UUID],
    ) -> NendoTrack:
        """Remove the track from the collection specified by collection_id.

        Args:
            collection_id (Union[str, uuid.UUID]): ID of the collection from which
                to remove the track.

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.remove_track_from_collection(
            track_id=self.id,
            collection_id=collection_id,
        )
        return self

    def process(self, plugin: str, **kwargs: Any) -> Union[NendoTrack, NendoCollection]:
        """Process the track with the specified plugin.

        Args:
            plugin (str): Name of the plugin to run on the track.

        Returns:
            Union[NendoTrack, NendoCollection]: The resulting track or collection,
                depending on what the plugin returns.
        """
        registered_plugin: RegisteredNendoPlugin = getattr(
            self.nendo_instance.plugins,
            plugin,
        )
        wrapped_method = get_wrapped_methods(registered_plugin.plugin_instance)

        if len(wrapped_method) > 1:
            raise NendoError(
                "Plugin has more than one wrapped method. Please use `nd.plugins.<plugin_name>.<method_name>` instead.",
            )
        return getattr(self.nendo_instance.plugins, plugin)(track=self, **kwargs)

    def export(self, file_path: str, file_format: str = "wav") -> NendoTrack:
        """Export the track to a file.

        Args:
            file_path (str): Path to the exported file. Can be either a full
                file path or a directory path. If a directory path is given,
                a filename will be automatically generated and the file will be
                exported to the format specified as file_format. If a full file
                path is given, the format will be deduced from the path and the
                file_format parameter will be ignored.
            file_format (str, optional): Format of the exported track. Ignored if
                file_path is a full file path. Defaults to "wav".

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.export_track(
            track_id=self.id,
            file_path=file_path,
            file_format=file_format,
        )
        return self

    def play(self):
        """Play the track."""
        play_signal(self.signal, self.sr)

    def loop(self):
        """Loop the track."""
        play_signal(self.signal, self.sr, loop=True)


class NendoTrackCreate(NendoTrackBase):  # noqa: D101
    pass


class NendoCollectionBase(BaseModel):  # noqa: D101
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        use_enum_values=True,
    )

    nendo_instance: Optional[Nendo] = None
    name: str
    description: str = ""
    collection_type: str = "collection"
    user_id: uuid.UUID
    visibility: Visibility = Visibility.private
    meta: Dict[str, Any] = Field(default_factory=dict)
    related_tracks: List[NendoTrackCollectionRelationship] = Field(default_factory=list)
    related_collections: List[NendoCollectionCollectionRelationship] = Field(
        default_factory=list,
    )

    def __init__(self, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(**kwargs)
        self.nendo_instance = Nendo()


class NendoCollection(NendoCollectionBase):
    """Basic class representing a nendo collection."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        output = f"id: {self.id}"
        output += f"\ntype: {self.collection_type}"
        output += f"\ndescription: {self.description}"
        output += f"\nuser id: {self.user_id}"
        output += f"\nvisibility: {self.visibility}"
        output += f"{pretty_print(self.meta)}"
        return output

    @classmethod
    def model_validate(cls, *args, **kwargs):  # noqa: D102
        instance = super().model_validate(*args, **kwargs)
        instance.nendo_instance = Nendo()
        return instance

    def __getitem__(self, index: int) -> NendoTrack:
        """Return the track at the specified index."""
        return self.tracks()[index]

    def __len__(self):
        """Return the number of tracks in the collection."""
        return len(self.tracks())

    def tracks(self) -> List[NendoTrack]:
        """Return all tracks listed in the collection.

        Collection will be loaded from the DB if not already loaded.

        Returns:
            List[NendoTrack]: List of tracks.
        """
        ts = self.__dict__.get("loaded_tracks")
        if ts is None:
            ts = self.nendo_instance.library.get_collection_tracks(self.id)
            self.__dict__["loaded_tracks"] = ts
        return ts

    def save(self) -> NendoCollection:
        """Save the collection to the nendo library.

        Returns:
            NendoCollection: The collection itself.
        """
        self.nendo_instance.library.update_collection(collection=self)
        return self

    def delete(
        self,
        remove_relationships: bool = False,
    ) -> NendoCollection:
        """Deletes the collection from the nendo library.

        Args:
            remove_relationships (bool, optional):
                If False prevent deletion if related tracks exist,
                if True delete relationships together with the object.
                Defaults to False.

        Returns:
            NendoCollection: The collection itself.
        """
        self.nendo_instance.library.remove_collection(
            collection_id=self.id,
            remove_relationships=remove_relationships,
        )
        return self

    def process(self, plugin: str, **kwargs: Any) -> NendoCollection:
        """Process the collection with the specified plugin.

        Args:
            plugin (str): Name of the plugin to run on the collection.

        Returns:
            NendoCollection: The collection that was created by the plugin.
        """
        registered_plugin: RegisteredNendoPlugin = getattr(
            self.nendo_instance.plugins,
            plugin,
        )
        wrapped_method = get_wrapped_methods(registered_plugin.plugin_instance)

        if len(wrapped_method) > 1:
            raise NendoError(
                "Plugin has more than one wrapped method. Please use `nd.plugins.<plugin_name>.<method_name>` instead.",
            )
        return getattr(self.nendo_instance.plugins, plugin)(collection=self, **kwargs)

    def has_relationship(self, relationship_type: str = "relationship") -> bool:
        """Check if the collection has the specified relationship type.

        Args:
            relationship_type (str): Type of the relationship to check for.
                Defaults to "relationship".

        Returns:
            bool: True if a relationship of the given type exists, False otherwise.
        """
        if self.related_collections is None:
            return False

        return any(
            r.relationship_type == relationship_type for r in self.related_collections
        )

    def has_relationship_to(self, collection_id: Union[str, uuid.UUID]) -> bool:
        """Check if the collection has a relationship to the specified collection ID."""
        collection_id = ensure_uuid(collection_id)
        if self.related_collections is None:
            return False

        return any(r.target_id == collection_id for r in self.related_collections)

    def add_track(
        self,
        track_id: Union[str, uuid.UUID],
        position: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Creates a relationship from the track to the collection.

        Args:
            track_id (Union[str, uuid.UUID]): ID of the track to add.
            position (int, optional): Target position of the track inside
                the collection.
            meta (Dict[str, Any]): Metadata of the relationship.

        Returns:
            NendoCollection: The collection itself.
        """
        updated_collection = self.nendo_instance.library.add_track_to_collection(
            track_id=track_id,
            collection_id=self.id,
            position=position,
            meta=meta,
        )
        self.related_tracks = updated_collection.related_tracks
        return self

    def remove_track(
        self,
        track_id: Union[str, uuid.UUID],
    ) -> NendoCollection:
        """Removes the track from the collection.

        Args:
            track_id (Union[str, uuid.UUID]): ID of the track to remove
                from the collection.

        Returns:
            NendoCollection: The collection itself.
        """
        self.nendo_instance.library.remove_track_from_collection(
            track_id=track_id,
            collection_id=self.id,
        )
        # NOTE the following removes _all_ relationships between the track and
        # the collection. In the future, this could be refined to account for cases
        # where multiple relationships of different types exist between a track
        # and a collection
        self.related_tracks = [t for t in self.related_tracks if t.id != track_id]
        return self

    def add_related_collection(
        self,
        track_ids: List[Union[str, uuid.UUID]],
        name: str,
        description: str = "",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> NendoCollection:
        """Create a new collection with a relationship to the current collection.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids.
            name (str): Name of the new related collection.
            description (str): Description of the new related collection.
            user_id (UUID, optional): The ID of the user adding the collection.
            relationship_type (str): Type of the relationship.
            meta (Dict[str, Any]): Meta of the new related collection.

        Returns:
            schema.NendoCollection: The newly added NendoCollection object.
        """
        self.nendo_instance.library.add_related_collection(
            track_ids=track_ids,
            collection_id=self.id,
            name=name,
            description=description,
            user_id=user_id,
            relationship_type=relationship_type,
            meta=meta,
        )
        return self

    def set_meta(self, meta: Dict[str, Any]) -> NendoCollection:
        """Set metadata of collection.

        Args:
            meta (Dict[str, Any]): Dictionary containing the metadata to be set.

        Returns:
            NendoCollection: The collection itself.
        """
        try:
            self.meta.update(meta)
            self.nendo_instance.library.update_collection(collection=self)
        except NendoError as e:
            logger.exception("Error updating meta: %s", e)
        return self

    def get_related_collections(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[NendoCollection]:
        """Get all collections to which the current collection has a relationship.

        Args:
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (Optional[str]): Key used for ordering the results.
            order (Optional[str]): Order in which to retrieve results ("asc" or "desc").
            limit (Optional[int]): Limit the number of returned results.
            offset (Optional[int]): Offset into the paginated results (requires limit).

        Returns:
            List[NendoCollection]: List containting all related NendoCollections
        """
        return self.nendo_instance.library.get_related_collections(
            track_id=self.id,
            user_id=user_id,
            order_by=order_by,
            order=order,
            limit=limit,
            offset=offset,
        )

    def has_meta(self, key: str) -> bool:
        """Check if a given collection has the given key in its meta dict.

        Args:
            key (str): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return any(k == key for k in self.meta)

    def get_meta(self, key: str) -> Dict[str, Any]:
        """Get the meta entry for the given key.

        Args:
            key (str): The key to get metadata for.

        Returns:
            Dict[str, Any]: Meta entry for given key.
        """
        if not self.has_meta(key):
            logger.error("Key not found in meta: %s", key)
            return None
        return self.meta[key]

    def remove_meta(self, key: str) -> NendoCollection:
        """Remove the meta entry for the given key.

        Args:
            key (str): The key to remove metadata for.

        Returns:
            NendoCollection: The track itself.
        """
        if not self.has_meta(key):
            logger.error("Key not found in meta: %s", key)
            return None
        _ = self.meta.pop(key, None)
        self.nendo_instance.library.update_collection(collection=self)
        return self

    def export(
        self,
        export_path: str,
        filename_suffix: str = "nendo",
        file_format: str = "wav",
    ) -> NendoCollection:
        """Export the collection to a directory.

        Args:
            export_path (str): Path to a directory into which the collection's tracks
                should be exported.
            filename_suffix (str): The suffix which should be appended to each
                exported track's filename.
            file_format (str, optional): Format of the exported track. Ignored if
                file_path is a full file path. Defaults to "wav".

        Returns:
            NendoTrack: The track itself.
        """
        self.nendo_instance.library.export_collection(
            collection_id=self.id,
            export_path=export_path,
            filename_suffix=filename_suffix,
            file_format=file_format,
        )
        return self


class NendoCollectionCreate(NendoCollectionBase):  # noqa: D101
    pass


class NendoPlugin(BaseModel, ABC):
    """Base class for all nendo plugins."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    nendo_instance: Nendo
    config: NendoConfig
    logger: logging.Logger
    plugin_name: str
    plugin_version: str

    # --------------
    # Decorators

    @staticmethod
    def stream_output(func):
        """Decorator to turn on streaming mode for functions.

        The requirement for this decorator to work on a function is that it would
        normally return a list.
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if self.config.stream_mode:
                return result
            # function is yielding single tracks if stream_chunk_size == 1
            elif self.config.stream_chunk_size > 1:  # noqa: RET505
                return [track for chunk in result for track in chunk]
            else:
                return list(result)

        return wrapper

    @staticmethod
    def batch_process(func):
        """Decorator to run functions multithreaded in batches.

        This decorator function transforms the given function to run
        in multiple threads. It expects that the first argument to the function
        is a list of items, which will be processed in parallel,
        in batches of a given size.
        """

        @functools.wraps(func)
        def wrapper(self, track=None, file_paths=None, *args, **kwargs):
            target = track or file_paths
            if isinstance(target, NendoTrack):
                return func(self, track=target, **kwargs)
            elif isinstance(target, list):  # noqa: RET505
                max_threads = self.config.max_threads
                batch_size = self.config.batch_size
                total = len(target)
                batches = [
                    target[i : i + batch_size] for i in range(0, total, batch_size)
                ]
                start_time = time.time()
                futures = []

                def run_batch(batch_index, batch):
                    try:
                        batch_start_time = time.time()
                        results = []
                        if track:
                            for _, item in enumerate(batch):
                                result = func(
                                    self,
                                    track=item,
                                    *args,  # noqa: B026
                                    **kwargs,
                                )
                                results.extend(result)
                        elif file_paths:
                            result = func(
                                self,
                                file_paths=batch,
                                *args,  # noqa: B026
                                **kwargs,
                            )
                            results.extend(result)
                        batch_end_time = time.time()
                        batch_time = time.strftime(
                            "%H:%M:%S",
                            time.gmtime(batch_end_time - batch_start_time),
                        )
                        total_elapsed_time = batch_end_time - start_time
                        average_time_per_batch = total_elapsed_time / (batch_index + 1)
                        estimated_total_time = average_time_per_batch * len(batches)
                        estimated_total_time_print = time.strftime(
                            "%H:%M:%S",
                            time.gmtime(estimated_total_time),
                        )
                        remaining_time = time.strftime(
                            "%H:%M:%S",
                            time.gmtime(estimated_total_time - total_elapsed_time),
                        )
                        logger.info(
                            f"Finished batch {batch_index + 1}/{len(batches)}.\n"
                            f"Time taken for this batch: {batch_time} - "
                            f"Estimated total time: {estimated_total_time_print} - "
                            f"Estimated remaining time: {remaining_time}\n",
                        )
                        return results
                    except NendoError as e:
                        logger.exception(
                            "Error processing batch %d: %s",
                            batch_index,
                            e,
                        )

                with ThreadPoolExecutor(max_workers=max_threads) as executor:
                    for batch_index, batch in enumerate(batches):
                        futures.append(executor.submit(run_batch, batch_index, batch))

                all_results = []
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        all_results.extend(future.result())
                return all_results
            else:
                raise TypeError("Expected NendoTrack or list of NendoTracks")

        return wrapper

    # ------------------

    def _get_track_or_collection_from_args(
        self,
        **kwargs,
    ) -> Tuple[Union[NendoTrack, NendoCollection], Dict]:
        """Get the track or collection from the kwargs."""
        track = kwargs.pop("track", None)
        if track is not None:
            return track, kwargs

        collection = kwargs.pop("collection", None)
        if collection is not None:
            return collection, kwargs

        track_or_collection_id = kwargs.pop("id", None)
        return (
            self.nendo_instance.library.get_track_or_collection(track_or_collection_id),
            kwargs,
        )

    def _run_default_wrapped_method(
        self,
        **kwargs: Any,
    ) -> Optional[Union[NendoTrack, NendoCollection]]:
        """Check if the plugin has a wrapped method and run it if it exists.

        If the plugin has more than one wrapped method, a warning is logged and
        None is returned.

        Returns:
            Optional[Union[NendoTrack, NendoCollection]]: The track or collection
                returned by the wrapped method.
        """
        # get the wrapped functions and ignore any methods of pydantic.BaseModel
        wrapped_methods = get_wrapped_methods(self)

        if len(wrapped_methods) > 1:
            warning_module = (
                inspect.getmodule(type(self))
                .__name__.split(".")[0]
                .replace("nendo_plugin_", "")
            )
            warning_methods = [
                f"nendo.plugins.{warning_module}.{m.__name__}()"
                for m in wrapped_methods
            ]
            self.logger.warning(
                f" Warning: Multiple wrapped methods found in plugin. Please call the plugin via one of the following methods: {', '.join(warning_methods)}.",
            )
            return None

        run_func = wrapped_methods[0]
        return run_func(self, **kwargs)

    @property
    def plugin_type(self) -> str:
        """Return type of plugin."""
        return "NendoPlugin"

    def __str__(self):
        return f"{self.plugin_type} | name: {self.name} | version: {self.version}"

    # batching is deactivated for now
    # @NendoPlugin.batch_process
    def __call__(self, **kwargs: Any) -> Optional[Union[NendoTrack, NendoCollection]]:
        """Call the plugin.

        Runs a registered run function of a plugin on a track, a collection, or a signal.
        If the plugin has more than one run function, a warning is raised and all the possible options are listed.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Optional[Union[NendoTrack, NendoCollection]]: The track or collection.
        """
        return self._run_default_wrapped_method(**kwargs)


class NendoBlobBase(BaseModel):  # noqa: D101
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        use_enum_values=True,
    )

    user_id: uuid.UUID
    resource: NendoResource
    visibility: Visibility = Visibility.private


class NendoBlobCreate(NendoBlobBase):  # noqa: D101
    pass


class NendoBlob(NendoBlobBase):
    """Class representing a blob object in Nendo.

    Used to store     binary data, e.g. large numpy matrices in
    the nendo library. Not used for storing waveforms,
    as they are considered native `NendoResource`s.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    data: Optional[bytes] = None

    class Config:  # noqa: D106
        from_attributes = True


class NendoStorage(BaseModel, ABC):
    """Basic class representing a Nendo storage driver."""

    @abstractmethod
    def init_storage_for_user(self, user_id: str) -> Any:
        """Initializes the storage location for the given user.

        Args:
            user_id (str): ID of the user for whom the storage is to be initialized.

        Returns:
            Any: Storage object
        """
        raise NotImplementedError

    @abstractmethod
    def generate_filename(self, filetype: str, user_id: str) -> str:
        """Generate a collision-free new filename.

        Args:
            filetype (str): The filetype to append (without the dot).
            user_id (str): The ID of the user requesting the file.

        Returns:
            str: The generated filename.
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, file_name: str, user_id: str) -> bool:
        """Check if the given file_name exists in the storage.

        Args:
            file_name (str): Name of the file for which to check existence
            user_id (str): User ID

        Returns:
            bool: True if it exists, false otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def as_local(self, file_path: str, location: ResourceLocation, user_id: str) -> str:
        """Get a local handle to the file.

        Return a file given as `file_path` as a locally accessible file,
        even if it originally resides in a remote storage location

        Args:
            file_path (str): Name of the file to obtain a local copy of.
            location (ResourceLocation): Location of the file, as provided by the
                corresponding NendoResource.
            user_id (str): User ID

        Returns:
            str: Local path to the original file (if it was local) or to a
                temporary copy (if it was remote)
        """
        raise NotImplementedError

    @abstractmethod
    def save_file(self, file_name: str, file_path: str, user_id: str) -> str:
        """Saves the file with the given file_name to the path specified by file_path.

        Args:
            file_name (str): The name of the target file.
            file_path (str): The path to the target file.
            user_id (str): The ID of the user requesting the file.

        Returns:
            str: The full path to the saved file resource.
        """
        raise NotImplementedError

    @abstractmethod
    def save_signal(
        self,
        file_name: str,
        signal: np.ndarray,
        sr: int,
        user_id: str,
    ) -> str:
        """Save a signal given as a numpy array to storage.

        Args:
            file_name (str): Name of the target file to save the signal to.
            signal (np.ndarray): The signal to write as a numpy array.
            sr (int): The sample rate of the signal.
            user_id (str): The ID of the user writing the file.

        Returns:
            str: The full path to the saved file resource.
        """
        raise NotImplementedError

    @abstractmethod
    def save_bytes(self, file_name: str, data: bytes, user_id: str) -> str:
        """Save a data given as bytes to the FS by pickling them first.

        Args:
            file_name (str): Name of the target file to save the data to.
            data (np.ndarray): The data to write to file in pickled form.
            user_id (str): The ID of the user writing the file.

        Returns:
            str: The full path to the saved file resource.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_file(self, file_name: str, user_id: str) -> bool:
        """Remove the file given by file_name and user_id from the storage.

        Args:
            file_name (str): Name of the file to remove.
            user_id (str): ID of the user requesting the removal.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_path(self, src: str, user_id: str) -> str:
        """Returns the path of a resource.

        Args:
            src (str): The full path to the resource.
            user_id (str): The ID of the user requesting the path.

        Returns:
            str: The resource path, minus the file name.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_name(self, src: str, user_id: str) -> str:
        """Returns the filename of a resource.

        Args:
            src (str): The full path to the resource.
            user_id (str): The ID of the user requesting the path.

        Returns:
            str: The resource file name, minus the path.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file(self, file_name: str, user_id: str) -> str:
        """Obtains the full path to the file by the name of file_name from storage.

        Args:
            file_name (str): The name of the target file.
            user_id (str): The ID of the user requesting the file.

        Returns:
            str: The full path to the file.
        """
        raise NotImplementedError

    @abstractmethod
    def list_files(self, user_id: str) -> List[str]:
        """Lists all files found in the user's library.

        Args:
            user_id (str): The ID of the user.

        Returns:
            List[str]: List of paths to files.
        """
        raise NotImplementedError

    @abstractmethod
    def get_bytes(self, file_name: str, user_id: str) -> Any:
        """Load the data bytes from the storage.

        Loading includes unpickling the file given as `file_name`.

        Args:
            file_name (str): Name of the target file to load.
            user_id (str): The ID of the user writing the file.

        Returns:
            The deserialized data bytes
        """
        raise NotImplementedError

    @abstractmethod
    def get_checksum(self, file_name: str, user_id: str) -> str:
        """Compute the checksum for the given file and user_id.

        Args:
            file_name (str): The name of the file in the library for which
                to compute the checksum.
            user_id (str): The ID of the user requesting the checksum.

        Returns:
            str: The checksum of the target file.
        """
        raise NotImplementedError

    @abstractmethod
    def get_driver_location(self) -> str:
        """Get the default resource location of the storage driver.

        e.g. "original", "local", "gcs", "s3", etc.

        Returns:
            str: Location type.
        """


class NendoStorageLocalFS(NendoStorage):
    """Implementation of the base storage driver for local filesystem access."""

    library_path: str = None

    def __init__(  # noqa: D107
        self,
        library_path: str,
        user_id: str,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.library_path = os.path.join(library_path, user_id)
        self.init_storage_for_user(user_id=user_id)

    def init_storage_for_user(self, user_id: str) -> str:  # noqa: ARG002
        """Initialize local storage for user."""
        if not os.path.isdir(self.library_path):
            logger.warning(
                f"Library path {self.library_path} does not exist, creating now.",
            )
            os.makedirs(self.library_path)
        return self.library_path

    def generate_filename(self, filetype: str, user_id: str) -> str:  # noqa: ARG002
        """Generate a unique filename."""
        return f"{uuid.uuid4()!s}.{filetype}"

    def file_exists(self, file_name: str, user_id: str) -> bool:
        """Check if the given file exists."""
        return os.path.isfile(self.get_file(file_name, user_id))

    def as_local(self, file_path: str, location: ResourceLocation, user_id: str) -> str:
        """Get a local handle to the file."""
        if location == self.get_driver_location():
            return self.get_file(os.path.basename(file_path), user_id)
        return file_path

    def save_file(self, file_name: str, file_path: str, user_id: str) -> str:
        """Copy the source file given by file_path to the library."""
        target_file = self.get_file(file_name=file_name, user_id=user_id)
        shutil.copy2(file_path, target_file)
        return target_file

    def save_signal(
        self,
        file_name: str,
        signal: np.ndarray,
        sr: int,
        user_id: str,  # noqa: ARG002
    ) -> str:
        """Save the given signal to storage."""
        target_file_path = self.get_file(file_name=file_name, user_id="")
        sf.write(target_file_path, signal, sr, subtype="PCM_16")
        return target_file_path

    def save_bytes(
        self,
        file_name: str,
        data: bytes,
        user_id: str,  # noqa: ARG002
    ) -> str:
        """Save the given bytes to storage."""
        target_file_path = self.get_file(file_name=file_name, user_id="")
        with open(target_file_path, "wb") as target_file:
            pickle.dump(data, target_file)
        return target_file_path

    def remove_file(self, file_name: str, user_id: str) -> bool:
        """Remove the given file."""
        target_file = self.get_file(file_name=file_name, user_id=user_id)
        try:
            os.remove(target_file)
            return True
        except OSError as e:
            logger.error("Removing file %s failed: %s", target_file, e)
            return False

    def get_file_path(self, src: str, user_id: str) -> str:  # noqa: ARG002
        """Get the path to the file (without the file name)."""
        return os.path.dirname(src)

    def get_file_name(self, src: str, user_id: str) -> str:  # noqa: ARG002
        """Get the file name (without the path)."""
        return os.path.basename(src)

    def get_file(self, file_name: str, user_id: str) -> str:  # noqa: ARG002
        """Get the full path to the file."""
        return os.path.join(self.library_path, file_name)

    def list_files(self, user_id: str) -> List[str]:  # noqa: ARG002
        """List all files contained in the storage."""
        with os.scandir(self.library_path) as entries:
            return [entry.name for entry in entries if entry.is_file()]

    def get_bytes(self, file_name: str, user_id: str) -> Any:
        """Get bytes from a stored file by unpickling it."""
        target_file_path = self.get_file(file_name=file_name, user_id=user_id)
        with open(target_file_path, "rb") as target_file:
            return pickle.loads(target_file.read())  # noqa: S301

    def get_checksum(self, file_name: str, user_id: str) -> str:
        """Compute the MD5 checksum of the given file."""
        return md5sum(self.get_file(file_name=file_name, user_id=user_id))

    def get_driver_location(self) -> ResourceLocation:
        """Get the default resource location of the storage driver."""
        return ResourceLocation.local


class RegisteredNendoPlugin(BaseModel):
    """A registered `NendoPlugin`.

    Used by the `NendoPluginRegistry` to manage `NendoPlugins`.
    """

    name: str
    version: str = "n/a"
    plugin_instance: NendoPlugin

    def __getattr__(self, func_name: str):
        try:
            attr = getattr(self.plugin_instance, func_name)
        except AttributeError:
            raise NendoPluginRuntimeError(
                f"Plugin {self.name} has no function {func_name}",
            ) from None
        if not callable(attr):
            return attr

        def method(*args, **kwargs):
            return attr(*args, **kwargs)

        return method

    def __call__(self, **kwargs: Any) -> Any:  # noqa: D102
        return self.plugin_instance(**kwargs)

    def __str__(self):
        return f"Nendo Library Plugin | name: {self.name} | version: {self.version}"


RegisteredNendoPlugin.model_rebuild()


class NendoPluginRegistry:
    """Class for registering and managing of nendo plugins."""

    _plugins: ClassVar[Dict[str, RegisteredNendoPlugin]] = {}

    def __getattr__(self, plugin_name: str):
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]
        if f"nendo_plugin_{plugin_name}" in self._plugins:
            return self._plugins[f"nendo_plugin_{plugin_name}"]
        raise AttributeError(f"Plugin '{plugin_name}' not found")

    def __str__(self):
        output = ""
        if not self._plugins:
            return "No plugins registered"
        output = f"{len(self._plugins)} registered plugins:"
        for k, v in self._plugins.items():
            output += "\n"
            output += f"{k} - {v.name} ({v.version})"
        return output

    def __call__(self):
        """Return string representation upon direct access to the registered plugin."""
        return self.__str__()

    def all_names(self) -> List[str]:
        """Return all plugins that are registered as a list of their names.

        Returns:
            List[str]: List containing all plugin names.
        """
        return [k for k, v in self._plugins.items()]

    def add(
        self,
        plugin_name: str,
        version: str,
        plugin_instance: NendoPlugin,
    ) -> RegisteredNendoPlugin:
        """Add a Registered plugin to the plugin registry.

        Args:
            plugin_name (str): Name of the plugin.
            version (str): Version of the plugin.
            plugin_instance (schema.NendoPlugin): Instantiated plugin class.

        Returns:
            RegisteredNendoPlugin: The registered nendo plugin.
        """
        self._plugins[plugin_name] = RegisteredNendoPlugin(
            name=plugin_name,
            version=version,
            plugin_instance=plugin_instance,
        )

    def remove(self, plugin_name: str) -> None:
        """Remove a plugin from the plugin registry.

        Args:
            plugin_name (str): Name of the plugin to remove.
        """
        del self._plugins[plugin_name]
