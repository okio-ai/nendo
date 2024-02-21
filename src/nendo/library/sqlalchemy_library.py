# -*- encoding: utf-8 -*-
# ruff: noqa: S603, S607, PLR2004
"""Module implementing the NendoLibraryPlugin using SQLAlchemy.

This module implements an SQLAlchemy version of the NendoLibraryPlugin.
The plugin is not suitable to be used by itself but should be inherited from
when implementing a new backend for the Nendo Library using SQLAlchemy. An example
is given by the DuckDB implementation used as the default Nendo Library.
"""

from __future__ import annotations

import logging
import os
import pickle
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

import librosa
import numpy as np
import soundfile as sf
from sqlalchemy import Float, and_, asc, desc, func, or_, true
from sqlalchemy.orm import Query, Session, joinedload, noload, sessionmaker
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.sqltypes import Text
from tinytag import TinyTag

from nendo import schema
from nendo.library import model
from nendo.utils import AudioFileUtils, ensure_uuid, md5sum

if TYPE_CHECKING:
    from pydantic import DirectoryPath, FilePath

logger = logging.getLogger("nendo")


class SqlAlchemyNendoLibrary(schema.NendoLibraryPlugin):
    """Implementation of the `NendoLibraryPlugin` using SQLAlchemy."""

    iter_index: int = 0
    user: schema.NendoUser = None

    def __init__(  # noqa: D107
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.iter_index = 0

    @property
    def default_user(self):
        """Default Nendo user."""
        return schema.NendoUser(
            id=uuid.UUID(self.config.user_id),
            name=self.config.user_name,
            password="nendo",  # noqa: S106
            email="info@okio.ai",
            verified=True,
        )

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = sessionmaker(autocommit=False, autoflush=False, bind=self.db)()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def __del__(self) -> None:
        self._disconnect()

    def _disconnect(self):
        """Close the connection to the database."""
        if hasattr(self, "db") and self.db is not None:
            self.db.dispose()

    def _ensure_user_uuid(self, user_id: Optional[Union[str, uuid.UUID]] = None):
        return ensure_uuid(user_id) if user_id is not None else self.user.id

    def _convert_plugin_data(self, value: Any, user_id: Optional[uuid.UUID] = None):
        # numpy matrices are stored as .npy blob and the blob ID is returned as
        # the plugin data value
        if isinstance(value, (np.ndarray, np.matrix)):
            with NamedTemporaryFile(suffix=".npy", delete=True) as tmpfile:
                np.save(tmpfile.name, value)
                blob = self.store_blob(file_path=tmpfile.name, user_id=user_id)
                return str(blob.id)
        try:
            return str(value)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to load plugin data: %s", e)

    # ==========================
    #
    # TRACK MANAGEMENT FUNCTIONS
    #
    # ==========================

    def __next__(self):
        with self.session_scope() as session:
            query = session.query(model.NendoTrackDB)
            track = query.offset(self.iter_index).first()
            if track:
                self.iter_index += 1
                return schema.NendoTrack.model_validate(track)
            raise StopIteration

    def _create_track_from_file(
        self,
        file_path: FilePath,
        track_type: str = "track",
        copy_to_library: Optional[bool] = None,
        skip_duplicate: Optional[bool] = None,
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoTrackCreate:
        """Create a NendoTrack from the file given by file_path.

        Args:
            file_path (Union[FilePath, str]): Path to the file to be added.
            track_type (str, optional): Type of the track. Defaults to "track".
            copy_to_library (bool, optional): Flag that specifies whether
                the file should be copied into the library directory.
                Defaults to None.
            skip_duplicate (bool, optional): Flag that specifies whether a
                file should be added that already exists in the library, based on its
                file checksum. Defaults to None.
            user_id (UUID, optional): ID of user adding the track.
            meta (dict, optional): Metadata to attach to the track upon adding.

        Returns:
            schema.NendoTrackCreate: The created NendoTrack.
        """
        if not os.path.isfile(file_path):
            raise schema.NendoResourceError("File not found", file_path)

        if not AudioFileUtils().is_supported_filetype(file_path):
            raise schema.NendoResourceError("Unsupported filetype", file_path)

        file_checksum = md5sum(file_path)
        file_stats = os.stat(file_path)
        user_id = self._ensure_user_uuid(user_id)

        # skip adding a duplicate based on config flag and hashsum of the file
        skip_duplicate = skip_duplicate or self.config.skip_duplicate
        if skip_duplicate:
            tracks = list(self.find_tracks(value=file_checksum))
            if len(tracks) > 0:
                return schema.NendoTrack.model_validate(tracks[0])

        meta = meta or {}
        resource_meta = {}

        # gather file metadata
        try:
            # extract ID3 tags
            tags = TinyTag.get(file_path)
            meta.update(tags.as_dict())
        except KeyError as e:
            logger.error(
                "Failed extracting tags from file: %s, Error: %s",
                file_path,
                e,
            )

        # convert and save to library
        copy_to_library = copy_to_library or self.config.copy_to_library
        if copy_to_library or (self.config.auto_convert and file_path.endswith(".mp3")):
            try:
                sr = None
                if self.config.auto_convert:
                    if file_path.endswith(".mp3"):
                        signal, sr = librosa.load(
                            path=file_path,
                            sr=None,
                            mono=False,
                        )
                    else:
                        signal, sr = sf.read(file=file_path)
                    # resample to default rate if required
                    if self.config.auto_resample and sr != self.config.default_sr:
                        logger.info(
                            "Auto-converting to SR of %d",
                            self.config.default_sr,
                        )
                        signal = librosa.resample(
                            signal,
                            orig_sr=sr,
                            target_sr=self.config.default_sr,
                        )
                        sr = self.config.default_sr
                    # sf.write expects the channels in the second dimension of the
                    # signal array! Librosa.load() loads them into the first dimension
                    signal = np.transpose(signal) if signal.shape[0] <= 2 else signal
                    path_in_library = self.storage_driver.save_signal(
                        file_name=self.storage_driver.generate_filename(
                            filetype="wav",
                            user_id=str(user_id),
                        ),
                        signal=signal,
                        sr=sr,
                        user_id=str(user_id),
                    )
                else:
                    # save file to storage in its original format
                    path_in_library = self.storage_driver.save_file(
                        file_name=self.storage_driver.generate_filename(
                            filetype=os.path.splitext(file_path)[1][1:],  # without dot
                            user_id=str(user_id),
                        ),
                        file_path=file_path,
                        user_id=str(user_id),
                    )

                # save the parsed sample rate
                if sr is not None:
                    meta["sr"] = sr
                    resource_meta["sr"] = sr

                location = self.storage_driver.get_driver_location()
            except Exception as e:  # noqa: BLE001
                raise schema.NendoLibraryError(
                    f"Error copying file to the library: {e}.",
                ) from e
        else:
            path_in_library = file_path
            location = schema.ResourceLocation.original

        resource_meta.update(
            {
                "original_filename": os.path.basename(file_path),
                "original_filepath": os.path.dirname(file_path),
                "original_size": file_stats.st_size,
                "original_checksum": file_checksum,
            },
        )

        if "title" not in meta or meta["title"] is None:
            meta.update({"title": os.path.basename(file_path)})

        resource = schema.NendoResource(
            file_path=self.storage_driver.get_file_path(
                src=path_in_library,
                user_id=str(user_id),
            ),
            file_name=self.storage_driver.get_file_name(
                src=path_in_library,
                user_id=str(user_id),
            ),
            resource_type="audio",
            location=location,
            meta=resource_meta,
        )
        return schema.NendoTrackCreate(
            nendo_instance=self.nendo_instance,
            resource=resource.model_dump(),
            user_id=user_id or self.user.id,
            track_type=track_type,
            meta=meta,
        )

    def _create_track_from_signal(
        self,
        signal: np.ndarray,
        sr: int,
        track_type: str = "track",
        meta: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> schema.NendoTrackCreate:
        """Create a NendoTrack from the given signal.

        Args:
            signal (np.ndarray): The numpy array containing the audio signal.
            sr (int): Sample rate
            track_type (str): Track type.
            user_id (UUID, optional): The ID of the user adding the track.
            meta (Dict[str, Any], optional): Track metadata. Defaults to {}.

        Returns:
            schema.NendoTrackCreate: The created NendoTrack.
        """
        target_file = None
        user_id = self._ensure_user_uuid(user_id)
        # sf.write expects the channels in the second dimension of the
        # signal array! Librosa.load() loads them into the first dimension
        signal = np.transpose(signal) if signal.shape[0] <= 2 else signal
        try:
            if self.config.auto_resample and sr != self.config.default_sr:
                logger.info("Auto-converting to SR of %d", self.config.default_sr)
                signal = librosa.resample(
                    signal,
                    orig_sr=sr,
                    target_sr=self.config.default_sr,
                )
                sr = self.config.default_sr
            target_file = self.storage_driver.save_signal(
                file_name=self.storage_driver.generate_filename(
                    filetype="wav",
                    user_id=str(user_id),
                ),
                signal=signal,
                sr=sr,
                user_id=str(user_id),
            )
        except Exception as e:  # noqa: BLE001
            raise schema.NendoLibraryError(
                f"Failed writing file {target_file} to the library. Error: {e}.",
            ) from None
        resource = schema.NendoResource(
            file_path=self.storage_driver.get_file_path(
                src=target_file,
                user_id=str(user_id),
            ),
            file_name=self.storage_driver.get_file_name(
                src=target_file,
                user_id=str(user_id),
            ),
            resource_type="audio",
            location=self.storage_driver.get_driver_location(),
        )
        # save sample rate
        meta = meta or {}
        meta["sr"] = sr
        return schema.NendoTrackCreate(
            resource=resource.model_dump(),
            user_id=user_id or self.user.id,
            track_type=track_type,
            meta=meta,
        )

    @schema.NendoPlugin.batch_process
    def _add_tracks_db(
        self,
        file_paths: List[FilePath],
        track_type: str = "track",
        copy_to_library: Optional[bool] = None,
        skip_duplicate: bool = True,
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[schema.NendoTrack]:
        """Add multiple tracks to the library from their file_paths.

        Args:
            file_paths (List[FilePath]): A list of full file paths to add as tracks.
            track_type (str, optional): The track_type of the tracks to add.
                Defaults to "track".
            copy_to_library (bool, optional): Flag that specifies whether
                the file should be copied into the library directory.
                Defaults to None.
            skip_duplicate (bool, optional): Flag that specifies whether a
                file should be added that already exists in the library, based on its
                file checksum. Defaults to None.
            user_id (UUID, optional): ID of user adding the track.
            meta (dict, optional): Metadata to attach to the track upon adding.

        Returns:
            List[schema.NendoTrack]: A list containing all added NendoTracks.
        """
        create_list = []
        for fp in file_paths:
            try:
                create_track = self._create_track_from_file(
                    file_path=fp,
                    track_type=track_type,
                    copy_to_library=copy_to_library,
                    skip_duplicate=skip_duplicate,
                    user_id=user_id or self.user.id,
                    meta=meta,
                )
                create_list.append(create_track)
            except schema.NendoLibraryError as e:
                logger.error("Failed adding file %s. Error: %s", fp, e)
        with self.session_scope() as session:
            db_tracks = self._upsert_tracks_db(tracks=create_list, session=session)
            return [schema.NendoTrack.model_validate(t) for t in db_tracks]

    from sqlalchemy import and_, or_

    def _get_related_tracks_query(
        self,
        track_id: uuid.UUID,
        session: Session,
        direction: str = "to",
        user_id: Optional[uuid.UUID] = None,
    ) -> Query:
        """Get tracks related to the track with track_id from the DB.

        Args:
            track_id (UUID): ID of the track to be searched for.
            session (Session): Session to be used for the transaction.
            user_id (UUID, optional): The user ID to filter for.
            direction (str, optional): The relationship direction
                (can be either one of "to", "from", "both").

        Returns:
            Query: The SQLAlchemy query object.
        """
        if direction == "to":
            query = (
                session.query(model.NendoTrackDB)
                .join(
                    model.TrackTrackRelationshipDB,
                    model.NendoTrackDB.id == model.TrackTrackRelationshipDB.source_id,
                )
                .filter(
                    and_(
                        model.NendoTrackDB.id != track_id,
                        model.TrackTrackRelationshipDB.target_id == track_id,
                    ),
                )
            )
        elif direction == "from":
            query = (
                session.query(model.NendoTrackDB)
                .join(
                    model.TrackTrackRelationshipDB,
                    model.NendoTrackDB.id == model.TrackTrackRelationshipDB.target_id,
                )
                .filter(
                    and_(
                        model.NendoTrackDB.id != track_id,
                        model.TrackTrackRelationshipDB.source_id == track_id,
                    ),
                )
            )
        elif direction == "both":
            query = (
                session.query(model.NendoTrackDB)
                .join(
                    model.TrackTrackRelationshipDB,
                    or_(
                        model.NendoTrackDB.id
                        == model.TrackTrackRelationshipDB.source_id,
                        model.NendoTrackDB.id
                        == model.TrackTrackRelationshipDB.target_id,
                    ),
                )
                .filter(
                    and_(
                        model.NendoTrackDB.id != track_id,
                        or_(
                            model.TrackTrackRelationshipDB.source_id == track_id,
                            model.TrackTrackRelationshipDB.target_id == track_id,
                        ),
                    ),
                )
            )
        else:
            raise ValueError(
                "Invalid direction value. Must be 'to', 'from', or 'both'.",
            )
        if user_id is not None:
            query = query.filter(model.NendoTrackDB.user_id == user_id)
        return query

    def _get_filtered_tracks_query(
        self,
        session: Session,
        query: Optional[Query] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_meta: Optional[List[str]] = None,
        track_type: Optional[Union[str, List[str]]] = None,
        user_id: Optional[uuid.UUID] = None,
        collection_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_names: Optional[List[str]] = None,
    ) -> Query:
        with session as session_local:
            if query:
                query_local = query
            else:
                query_local = session_local.query(model.NendoTrackDB)
                if user_id is not None:
                    query_local = query_local.filter(
                        model.NendoTrackDB.user_id == user_id,
                    )
            plugin_name_condition = true()
            if (
                plugin_names is not None
                and isinstance(plugin_names, list)
                and len(plugin_names) > 0
            ):
                plugin_name_condition = model.NendoPluginDataDB.plugin_name.in_(
                    plugin_names,
                )

            # apply track type filter if applicable
            if track_type is not None:
                if isinstance(track_type, list):
                    query_local = query_local.filter(
                        model.NendoTrackDB.track_type.in_(track_type),
                    )
                else:
                    query_local = query_local.filter(
                        model.NendoTrackDB.track_type == track_type,
                    )

            # apply collection filter if applicable
            if collection_id is not None:
                collection_id = ensure_uuid(collection_id)

                query_local = query_local.join(
                    model.TrackCollectionRelationshipDB,
                    model.NendoTrackDB.id
                    == model.TrackCollectionRelationshipDB.source_id,
                ).filter(
                    model.TrackCollectionRelationshipDB.target_id == collection_id,
                )

            # apply resource filters if applicable
            if search_meta and len(search_meta) > 0:
                search_filter = and_(
                    *(
                        or_(
                            cast(model.NendoTrackDB.meta, Text()).ilike(
                                "%{}%".format(str(value)),
                            ),
                            cast(model.NendoTrackDB.resource, Text()).ilike(
                                "%{}%".format(str(value)),
                            ),
                        )
                        for value in search_meta
                    ),
                )
                query_local = query_local.filter(search_filter)

            # apply plugin data filters
            if filters is not None:
                for k, v in filters.items():
                    if v is None:
                        continue

                    # range
                    if type(v) == tuple:
                        query_local = query_local.filter(
                            model.NendoTrackDB.plugin_data.any(
                                and_(
                                    plugin_name_condition,
                                    model.NendoPluginDataDB.key == k,
                                    cast(model.NendoPluginDataDB.value, Float)
                                    >= cast(v[0], Float),
                                    cast(model.NendoPluginDataDB.value, Float)
                                    <= cast(v[1], Float),
                                ),
                            ),
                        )
                    # multiselect
                    elif isinstance(v, list):
                        sv = [str(vi) for vi in v]
                        query_local = query_local.filter(
                            model.NendoTrackDB.plugin_data.any(
                                and_(
                                    plugin_name_condition,
                                    model.NendoPluginDataDB.key == k,
                                    model.NendoPluginDataDB.value.in_(sv),
                                ),
                            ),
                        )
                    # fuzzy match
                    else:
                        query_local = query_local.filter(
                            model.NendoTrackDB.plugin_data.any(
                                and_(
                                    plugin_name_condition,
                                    model.NendoPluginDataDB.key == k,
                                    cast(model.NendoPluginDataDB.value, Text()).ilike(
                                        "%{}%".format(str(v)),
                                    ),
                                ),
                            ),
                        )
            return query_local

    def _upsert_track_track_relationship(
        self,
        relationship: schema.NendoRelationshipBase,
        session: Session,
    ) -> schema.NendoTrack:
        """Insert or replace a track-to-track relationship in the database.

        Args:
            relationship (schema.NendoRelationshipBase): The relationship to upsert.
            session (sqlalchemy.Session): Session object to commit to.

        Returns:
            schema.NendoTrack: The upserted NendoTrack.
        """
        if type(relationship) == schema.NendoRelationshipCreate:
            # creating new relationship
            db_rel = model.TrackTrackRelationshipDB(**relationship.model_dump())
            session.add(db_rel)
        else:
            # updating existing relationship
            db_rel = (
                session.query(model.TrackTrackRelationshipDB)
                .filter_by(id=relationship.id)
                .first()
            )
            db_rel.source_id = relationship.source_id
            db_rel.target_id = relationship.target_id
            db_rel.relationship_type = relationship.relationship_type
            db_rel.meta = relationship.meta
        session.commit()
        return db_rel

    def _upsert_track_db(
        self,
        track: schema.NendoTrackBase,
        session: Session,
    ) -> model.NendoTrackDB:
        """Create track in DB or update if it exists.

        Args:
            track (schema.NendoTrackBase): Track object to be created
            session (Session): Session to be used for the transaction

        Returns:
            model.NendoTrackDB: The ORM model object of the upserted track
        """
        if type(track) == schema.NendoTrackCreate:
            # create new track
            track_dict = track.model_dump()
            track_dict.pop("nendo_instance")
            db_track = model.NendoTrackDB(**track_dict)
            session.add(db_track)
        else:
            # update existing track
            db_track = (
                session.query(model.NendoTrackDB).filter_by(id=track.id).one_or_none()
            )
            if db_track is None:
                raise schema.NendoTrackNotFoundError("Track not found", id=track.id)
            db_track.user_id = track.user_id
            db_track.visibility = track.visibility
            db_track.resource = track.resource.model_dump()
            db_track.track_type = track.track_type
            db_track.images = track.images
            db_track.meta = track.meta
        session.commit()
        return db_track

    def _upsert_tracks_db(
        self,
        tracks: List[schema.NendoTrackBase],
        session: Session,
    ) -> List[model.NendoTrackDB]:
        """Create multiple tracks in DB or update if it exists.

        Args:
            tracks (List[schema.NendoTrackCreate]): Track object to be created
            session (Session): Session to be used for the transaction

        Returns:
            List[model.NendoTrackDB]: The ORM model objects of the upserted tracks
        """
        db_tracks = []
        for track in tracks:
            if type(track) == schema.NendoTrackCreate:
                # create new track
                track_dict = track.model_dump()
                track_dict.pop("nendo_instance")
                db_tracks.append(model.NendoTrackDB(**track_dict))
            else:
                # update existing track
                db_tracks.append(
                    session.query(
                        model.NendoTrackDB,
                    )
                    .filter_by(
                        id=track.id,
                    )
                    .one_or_none(),
                )
                db_track = db_tracks[-1]
                if db_track is None:
                    raise schema.NendoTrackNotFoundError(
                        "Track not found",
                        id=track.id,
                    )
                db_track.user_id = track.user_id
                db_track.visibility = track.visibility
                db_track.resource = track.resource.model_dump()
                db_track.track_type = track.track_type
                db_track.images = track.images
                db_track.meta = track.meta
        session.add_all(db_tracks)
        session.commit()
        return db_tracks

    def _get_plugin_data_db(
        self,
        track_id: uuid.UUID,
        user_id: uuid.UUID,
        session: Session,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
        key: Optional[str] = None,
    ) -> List[model.NendoPluginDataDB]:
        """Get all plugin data related to a track from the DB.

        Args:
            track_id (UUID): Track ID to get the related plugin data for.
            user_id (UUID): The user ID to filter for.
            session (Session): SQLAlchemy session.
            plugin_name (str, optional): The name of the plugin with which
                the plugin data was created.
            plugin_version (str, optional): The version of the plugin with which
                the plugin data was created.
            key (str, optional): The key for which to filter the plugin data.

        Returns:
            List[model.NendoPluginDataDB]: List of nendo plugin data entries.
        """
        with session as session_local:
            plugin_data_db = session_local.query(model.NendoPluginDataDB).filter(
                and_(
                    model.NendoPluginDataDB.track_id == track_id,
                    model.NendoPluginDataDB.user_id == user_id,
                ),
            )
            if plugin_name is not None:
                plugin_data_db = plugin_data_db.filter(
                    model.NendoPluginDataDB.plugin_name == plugin_name,
                )
            if plugin_version is not None:
                plugin_data_db = plugin_data_db.filter(
                    model.NendoPluginDataDB.plugin_version == plugin_version,
                )
            if key is not None:
                plugin_data_db = plugin_data_db.filter(
                    model.NendoPluginDataDB.key == key,
                )
            return plugin_data_db.all()

    def get_plugin_data(
        self,
        track_id: Union[str, uuid.UUID],
        user_id: Optional[Union[str, uuid.UUID]] = None,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
        key: Optional[str] = None,
    ) -> List[schema.NendoPluginData]:
        """Get all plugin data related to a track from the DB.

        Args:
            track_id (UUID): Track ID to get the related plugin data for.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            plugin_name (str, optional): The name of the plugin with which
                the plugin data was created.
            plugin_version (str, optional): The version of the plugin with which
                the plugin data was created.
            key (str, optional): The key for which to filter the plugin data.

        Returns:
            List[NendoPluginData]: List of nendo plugin data entries.
        """
        track_id = ensure_uuid(track_id)
        user_id = self._ensure_user_uuid(user_id=user_id)
        with self.session_scope() as session:
            plugin_data_db = self._get_plugin_data_db(
                track_id=track_id,
                user_id=user_id,
                session=session,
                plugin_name=plugin_name,
                plugin_version=plugin_version,
                key=key,
            )
            return [
                schema.NendoPluginData.model_validate(pdb) for pdb in plugin_data_db
            ]

    def _get_latest_plugin_data_db(
        self,
        track_id: uuid.UUID,
        plugin_name: str,
        plugin_version: str,
        key: str,
        session: Session,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[model.NendoPluginDataDB]:
        """Get the latest plugin data for a given track id, plugin name and data key.

        Args:
            track_id (uuid.UUID):  Track ID to get the related plugin data for.
            plugin_name (str): Name of the plugin to get related data for.
            plugin_version (str): Version of the plugin to get related data for.
            key (str): Key by which to filter the plugin data.
            session (Session): SQLAlchemy session.
            user_id (UUID, optional): The user ID to filter for.

        Returns:
            model.NendoPluginDataDB: A single nendo plugin data entry.
        """
        user_id = self._ensure_user_uuid(user_id)
        s = session or self.session_scope()
        with s as session_local:
            plugin_data_db = session_local.query(model.NendoPluginDataDB).filter(
                and_(
                    model.NendoPluginDataDB.track_id == track_id,
                    model.NendoPluginDataDB.plugin_name == plugin_name,
                    model.NendoPluginDataDB.plugin_version == plugin_version,
                    model.NendoPluginDataDB.key == key,
                ),
            )

            if user_id is not None:
                plugin_data_db = plugin_data_db.filter(
                    model.NendoPluginDataDB.user_id == user_id,
                )
            plugin_data_db = plugin_data_db.order_by(
                model.NendoPluginDataDB.updated_at.desc(),
            ).first()
            return plugin_data_db if plugin_data_db is not None else None

    def _insert_plugin_data_db(
        self,
        plugin_data: schema.NendoPluginDataCreate,
        session: Session,
    ) -> model.NendoPluginDataDB:
        db_plugin_data = model.NendoPluginDataDB(**plugin_data.model_dump())
        session.add(db_plugin_data)
        session.commit()
        return db_plugin_data

    def _update_plugin_data_db(
        self,
        existing_plugin_data: model.NendoPluginDataDB,
        plugin_data: schema.NendoPluginData,
        session: Session,
    ) -> model.NendoPluginDataDB:
        if existing_plugin_data is None:
            logger.error("Plugin data not found!")
            return None
        existing_plugin_data.key = plugin_data.key
        existing_plugin_data.value = plugin_data.value
        existing_plugin_data.user_id = plugin_data.user_id
        session.commit()
        return existing_plugin_data

    def create_object(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_type: str = "text",
        meta: Optional[Dict[str, Any]] = None,
        visibility: schema.Visibility = schema.Visibility.private,
        images: Optional[List[schema.NendoResource]] = None,
        file_path: str = "",
        resource_type: schema.ResourceType = schema.ResourceType.text,
        resource_meta: Optional[Dict[str, Any]] = None,
        copy_to_library: Optional[bool] = None,
    ) -> schema.NendoTrack:
        """Create a new object, manually.

        Args:
            user_id (uuid.UUID, optional): The ID of the object's user.
            track_type (str): The type of the object. Defaults to "track".
            meta (Dict[str, Any], optional): Metadata about the object.
            visibility (Visibility): Visibility of the object. Defaults to "private".
            images (List[NendoResource], optional): List of (additional) images for
                the object.
            file_path (str): Path to a file to be added to the track as NendoResource.
                Defaults to "" (no file path).
            resource_type (ResourceType): Type of the resource to set.
                Defaults to "text".
            resource_meta (dict, optional): Metadata about the NendoResource.
            copy_to_library (bool, optional): Flag that determines, whether to copy
                the file to the library storage or not.

        Returns:
            NendoTrack: The created track.
        """
        user_id = self._ensure_user_uuid(user_id)
        resource = None
        if len(file_path) > 0:
            copy_to_library = copy_to_library or self.config.copy_to_library
            if copy_to_library:
                try:
                    # save file to storage in its original format
                    path_in_library = self.storage_driver.save_file(
                        file_name=self.storage_driver.generate_filename(
                            filetype=os.path.splitext(file_path)[1][1:],  # without dot
                            user_id=str(user_id),
                        ),
                        file_path=file_path,
                        user_id=str(user_id),
                    )
                    location = self.storage_driver.get_driver_location()
                except Exception as e:  # noqa: BLE001
                    raise schema.NendoLibraryError(
                        f"Error copying file to the library: {e}.",
                    ) from e
            else:
                path_in_library = file_path
                location = schema.ResourceLocation.original

            resource = schema.NendoResource(
                file_path=self.storage_driver.get_file_path(
                    src=path_in_library,
                    user_id=str(user_id),
                ),
                file_name=self.storage_driver.get_file_name(
                    src=path_in_library,
                    user_id=str(user_id),
                ),
                resource_type=resource_type,
                location=location,
                meta=resource_meta or {},
            )
        else:
            location = self.storage_driver.get_driver_location()
            resource = schema.NendoResource(
                file_path="",
                file_name="",
                resource_type=resource_type,
                location=location,
                meta=resource_meta or {},
            )
        track = schema.NendoTrackCreate(
            user_id=user_id,
            visibility=visibility,
            images=images or [],
            resource=resource.model_dump(),
            track_type=track_type,
            meta=meta or {},
        )
        with self.session_scope() as session:
            db_track = self._upsert_track_db(track=track, session=session)
            return schema.NendoTrack.model_validate(db_track)

    def add_track(
        self,
        file_path: Union[FilePath, str],
        track_type: str = "track",
        copy_to_library: Optional[bool] = None,
        skip_duplicate: Optional[bool] = None,
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoTrack:
        """Add the track given by path to the library.

        Args:
            file_path (Union[FilePath, str]): Path to the file to be added.
            track_type (str, optional): Type of the track. Defaults to "track".
            copy_to_library (bool, optional): Flag that specifies whether
                the file should be copied into the library directory.
                Defaults to None.
            skip_duplicate (bool, optional): Flag that specifies whether a
                file should be added that already exists in the library, based on its
                file checksum. Defaults to None.
            user_id (UUID, optional): ID of user adding the track.
            meta (dict, optional): Metadata to attach to the track upon adding.

        Returns:
            schema.NendoTrack: The track that was added to the library.
        """
        skip_duplicate = skip_duplicate or self.config.skip_duplicate
        track = self._create_track_from_file(
            file_path=file_path,
            track_type=track_type,
            copy_to_library=copy_to_library,
            skip_duplicate=skip_duplicate,
            user_id=user_id or self.user.id,
            meta=meta,
        )
        if track is not None:
            with self.session_scope() as session:
                db_track = self._upsert_track_db(track=track, session=session)
                track = schema.NendoTrack.model_validate(db_track)
        return track

    def add_track_from_signal(
        self,
        signal: np.ndarray,
        sr: int,
        track_type: str = "track",
        user_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoTrack:
        """Add a track to the library that is described by the given signal.

        Args:
            signal (np.ndarray): The numpy array containing the audio signal.
            sr (int): Sample rate
            track_type (str): Track type.
            user_id (UUID, optional): The ID of the user adding the track.
            meta (Dict[str, Any], optional): Track metadata. Defaults to {}.

        Returns:
            schema.NendoTrack: The added NendoTrack
        """
        track = self._create_track_from_signal(
            signal=signal,
            sr=sr,
            track_type=track_type,
            meta=meta,
            user_id=user_id or self.user.id,
        )
        if track is not None:
            with self.session_scope() as session:
                db_track = self._upsert_track_db(track=track, session=session)
                track = schema.NendoTrack.model_validate(db_track)
        return track

    def add_tracks(
        self,
        path: Union[str, DirectoryPath],
        track_type: str = "track",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        copy_to_library: Optional[bool] = None,
        skip_duplicate: bool = True,
    ) -> schema.NendoCollection:
        """Scan the provided path and upsert the information into the library.

        Args:
            path (Union[str, DirectoryPath]): Path to the directory to be scanned
            track_type (str, optional): Track type for the new tracks
            user_id (UUID, optional): The ID of the user adding the track.
            copy_to_library (bool): Copy and convert the data into the nendo Library?
            skip_duplicate (bool): Skip adding duplicates?

        Returns:
            tracks (list[NendoTrack]): The tracks that were added to the Library
        """
        user_id = self._ensure_user_uuid(user_id)
        file_list = []
        if not os.path.exists(path):
            raise schema.NendoLibraryError(f"Source directory {path} does not exist.")
        for root, _, files in os.walk(path):
            file_list.extend(
                [
                    os.path.join(root, file)
                    for file in files
                    if AudioFileUtils().is_supported_filetype(file)
                ],
            )
        tracks = self._add_tracks_db(
            file_paths=file_list,
            track_type=track_type,
            copy_to_library=copy_to_library,
            skip_duplicate=skip_duplicate,
            user_id=user_id,
        )
        return self.add_collection(name=path, track_ids=[t.id for t in tracks])

    def add_track_relationship(
        self,
        track_one_id: Union[str, uuid.UUID],
        track_two_id: Union[str, uuid.UUID],
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a relationship between two tracks."""
        track_one = self.get_track(track_one_id)  # track
        track_two = self.get_track(track_two_id)  # related

        # check that tracks are not the same
        if track_one_id == track_two_id:
            logger.error("Error must provide two different existing track ids")
            return False

        # check if tracks exist
        if track_one is None:
            logger.error("Error track id %s not found", str(track_one_id))
            return False

        if track_two is None:
            logger.error("Error track id %s not found", str(track_two_id))
            return False

        relationship = schema.NendoRelationshipCreate(
            source_id=track_one.id,
            target_id=track_two.id,
            relationship_type=relationship_type,
            meta=meta or {},
        )
        with self.session_scope() as session:
            relationship = schema.NendoRelationship.model_validate(
                self._upsert_track_track_relationship(
                    relationship=relationship,
                    session=session,
                ),
            )
        return True

    def add_related_track(
        self,
        file_path: Union[FilePath, str],
        related_track_id: Union[str, uuid.UUID],
        track_type: str = "str",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_meta: Optional[Dict[str, Any]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoTrack:
        """Add a track from a file with a relationship to another track."""
        user_id = self._ensure_user_uuid(user_id=user_id)
        related_track_id = ensure_uuid(related_track_id)
        track = self.add_track(
            file_path=file_path,
            track_type=track_type,
            user_id=user_id,
            meta=track_meta,
        )
        relationship = schema.NendoRelationshipCreate(
            source_id=track.id,
            target_id=related_track_id,
            relationship_type=relationship_type,
            meta=meta or {},
        )
        with self.session_scope() as session:
            relationship = schema.NendoRelationship.model_validate(
                self._upsert_track_track_relationship(
                    relationship=relationship,
                    session=session,
                ),
            )
        return track

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
    ) -> schema.NendoTrack:
        """Add a track from a signal with a relationship to another track."""
        user_id = self._ensure_user_uuid(user_id)
        related_track_id = ensure_uuid(related_track_id)
        track = self.add_track_from_signal(
            signal=signal,
            sr=sr,
            track_type=track_type,
            meta=track_meta,
        )
        relationship = schema.NendoRelationshipCreate(
            source_id=track.id,
            target_id=related_track_id,
            relationship_type=relationship_type,
            meta=meta or {},
        )
        with self.session_scope() as session:
            relationship = schema.NendoRelationship.model_validate(
                self._upsert_track_track_relationship(
                    relationship=relationship,
                    session=session,
                ),
            )
        return track

    def update_track(
        self,
        track: schema.NendoTrack,
    ) -> schema.NendoTrack:
        """Updates the given track by storing it to the database.

        Args:
            track (NendoTrack): The track to be stored to the database.

        Raises:
            NendoTrackNotFoundError: If the track passed to the function
                does not exist in the database.

        Returns:
            NendoTrack: The updated track.
        """
        with self.session_scope() as session:
            # update existing track
            db_track = (
                session.query(model.NendoTrackDB).filter_by(id=track.id).one_or_none()
            )
            if db_track is None:
                raise schema.NendoTrackNotFoundError("Track not found", id=track.id)
            db_track.user_id = track.user_id
            db_track.visibility = track.visibility
            db_track.resource = track.resource.model_dump()
            db_track.track_type = track.track_type
            db_track.images = track.images
            db_track.meta = track.meta
            session.commit()
        return db_track

    def add_plugin_data(
        self,
        track_id: Union[str, uuid.UUID],
        key: str,
        value: Any,
        plugin_name: str,
        plugin_version: Optional[str] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        replace: Optional[bool] = None,
    ) -> schema.NendoPluginData:
        """Add plugin data to a NendoTrack and persist changes into the DB.

        Args:
            track_id (Union[str, UUID]): ID of the track to which
                the plugin data should be added.
            key (str): Key under which to save the data.
            value (Any): Data to save.
            plugin_name (str): Name of the plugin.
            plugin_version (str, optional): Version of the plugin. If none is given,
                the currently loaded version of the plugin given by `plugin_name`
                will be used.
            user_id (Union[str, UUID], optional): ID of user adding the plugin data.
            replace (bool, optional): Flag that determines whether
                the last existing data point for the given plugin name and -version
                is overwritten or not. If undefined, the nendo configuration's
                `replace_plugin_data` value will be used.

        Returns:
            NendoPluginData: The saved plugin data as a NendoPluginData object.
        """
        # create plugin data
        user_id = self._ensure_user_uuid(user_id)
        replace = (
            replace
            if replace is not None
            else self.nendo_instance.config.replace_plugin_data
        )
        value_converted = self._convert_plugin_data(value=value, user_id=user_id)
        if plugin_version is None:
            try:
                plugin = getattr(self.nendo_instance.plugins, plugin_name)
            except AttributeError as e:  # noqa: F841
                self.logger.error(
                    f"Plugin with name {plugin_name} is not loaded. "
                    "You have to manually specify the plugin_version parameter.",
                )
                return None
            plugin_version = plugin.version
        plugin_data = schema.NendoPluginDataCreate(
            track_id=ensure_uuid(track_id),
            user_id=user_id,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            key=key,
            value=value_converted,
        )
        with self.session_scope() as session:
            existing_plugin_data = self._get_latest_plugin_data_db(
                track_id=track_id,
                plugin_name=plugin_name,
                plugin_version=plugin_version,
                key=key,
                session=session,
                user_id=user_id,
            )
            if replace is True:
                if existing_plugin_data is not None:
                    db_plugin_data = self._update_plugin_data_db(
                        existing_plugin_data=existing_plugin_data,
                        plugin_data=plugin_data,
                        session=session,
                    )
                else:
                    db_plugin_data = self._insert_plugin_data_db(
                        plugin_data=plugin_data,
                        session=session,
                    )
            else:
                db_plugin_data = self._insert_plugin_data_db(
                    plugin_data=plugin_data,
                    session=session,
                )
            return schema.NendoPluginData.model_validate(db_plugin_data)

    def get_track(
        self,
        track_id: uuid.UUID,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> schema.NendoTrack:
        """Get a single track from the library by ID."""
        with self.session_scope() as session:
            query = session.query(model.NendoTrackDB).filter(
                model.NendoTrackDB.id == track_id,
            )

            if user_id is not None:
                user_id = self._ensure_user_uuid(user_id)
                query = query.filter(model.NendoTrackDB.user_id == user_id)

            track_db = query.one_or_none()
            return (
                schema.NendoTrack.model_validate(track_db)
                if track_db is not None
                else None
            )

    @schema.NendoPlugin.stream_output
    def get_tracks(
        self,
        query: Optional[Query] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        load_related_tracks: bool = False,
        session: Optional[Session] = None,
    ) -> Union[List, Iterator]:
        """Get tracks based on the given query parameters.

        Args:
            query (Query, optional): Query object to build from.
            user_id (Union[str, UUID], optional): ID of user to filter tracks by.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).
            load_related_tracks (bool, optional): Flag that determines whether to
                populate related_tracks field.
            session (sqlalchemy.Session): Session object to commit to.

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        user_id = self._ensure_user_uuid(user_id)
        s = session or self.session_scope()
        with s as session_local:
            if query:
                query_local = query
            else:
                query_local = session_local.query(model.NendoTrackDB).filter(
                    model.NendoTrackDB.user_id == user_id,
                )
                if user_id is not None:
                    query_local = query_local.filter(
                        model.NendoTrackDB.user_id == user_id,
                    )
            if order_by:
                if order_by == "random":
                    query_local = query_local.order_by(func.random())
                elif order_by == "collection":
                    if order == "desc":
                        query_local = query_local.order_by(
                            desc(
                                model.TrackCollectionRelationshipDB.relationship_position,
                            ),
                        )
                    else:
                        query_local = query_local.order_by(
                            asc(
                                model.TrackCollectionRelationshipDB.relationship_position,
                            ),
                        )
                elif order == "desc":
                    query_local = query_local.order_by(
                        desc(getattr(model.NendoTrackDB, order_by)),
                    )
                else:
                    query_local = query_local.order_by(
                        asc(getattr(model.NendoTrackDB, order_by)),
                    )
            if limit:
                query_local = query_local.limit(limit)
                if offset:
                    query_local = query_local.offset(offset)

            if not load_related_tracks:
                query_local = query_local.options(
                    noload(model.NendoTrackDB.related_tracks),
                )

            if self.config.stream_chunk_size > 1:
                chunk = []
                for track in query_local:
                    chunk.append(schema.NendoTrack.model_validate(track))
                    if len(chunk) == self.config.stream_chunk_size:
                        yield chunk
                        chunk = []
                if chunk:  # yield remaining tracks in non-full chunk
                    yield chunk
            else:
                for track in query_local:
                    yield schema.NendoTrack.model_validate(track)

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
            track_id (Union[str, UUID]): ID of the track to be searched for.
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
        with self.session_scope() as session:
            query = self._get_related_tracks_query(
                track_id=ensure_uuid(track_id),
                session=session,
                direction=direction,
                user_id=user_id,
            )
            return self.get_tracks(
                query=query,
                order_by=order_by,
                order=order,
                limit=limit,
                offset=offset,
                load_related_tracks=True,
                session=session,
            )

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
            direction (str, optional): The relationship direction ("to", "from", "both").
            filters (dict, optional): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict, optional): Dictionary containing the keywords to search
                for over the track.resource.meta field. The dictionary's values
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
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = self._get_related_tracks_query(
                track_id=ensure_uuid(track_id),
                session=session,
                direction=direction,
                user_id=user_id,
            )
            query = self._get_filtered_tracks_query(
                session=session,
                query=query,
                filters=filters,
                search_meta=search_meta,
                track_type=track_type,
                user_id=user_id,
                collection_id=collection_id,
                plugin_names=plugin_names,
            )
            return self.get_tracks(
                query=query,
                order_by=order_by,
                order=order,
                limit=limit,
                offset=offset,
                load_related_tracks=True,
                session=session,
            )

    def find_tracks(
        self,
        value: str,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[List, Iterator]:
        """Obtain tracks from the db by fulltext search.

        Args:
            value (str): The value to search for. The value is matched against
                text representations of the track's `meta` and `resource` fields.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of tracks, depending on the
                configuration variable stream_mode
        """
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = session.query(model.NendoTrackDB).filter(
                or_(
                    cast(model.NendoTrackDB.resource, Text()).ilike(
                        "%{}%".format(value),
                    ),
                    cast(model.NendoTrackDB.meta, Text()).ilike(
                        "%{}%".format(value),
                    ),
                ),
            )
            if user_id is not None:
                query = query.filter(model.NendoTrackDB.user_id == user_id)
            return self.get_tracks(
                query=query,
                order_by=order_by,
                order=order,
                limit=limit,
                offset=offset,
                load_related_tracks=False,
                session=session,
            )

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
        session: Optional[Session] = None,
    ) -> Union[List, Iterator]:
        """Obtain tracks from the db by filtering over plugin data.

        Args:
            filters (dict, optional): Dictionary containing the filters to apply.
                Defaults to None.
            search_meta (dict, optional): Dictionary containing the keywords to
                search for over the `track.meta` and `track.resource` fields.
                The dictionary's values should contain singular search tokens
                and the keys currently have no effect but might in other
                implementations of the NendoLibrary. Defaults to {}.
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
        user_id = self._ensure_user_uuid(user_id)
        s = session or self.session_scope()
        with s as session_local:
            """Obtain tracks from the db by filtering w.r.t. various fields."""
            query = self._get_filtered_tracks_query(
                session=session_local,
                filters=filters,
                search_meta=search_meta,
                track_type=track_type,
                user_id=user_id,
                collection_id=collection_id,
                plugin_names=plugin_names,
            )
            return self.get_tracks(
                query=query,
                order_by=order_by,
                order=order,
                limit=limit,
                offset=offset,
                load_related_tracks=False,
                session=session_local,
            )

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
            track_id (Union[str, uuid.UUID]): The ID of the track to remove
            user_id (Union[str, UUID], optional): The ID of the user
            remove_relationships (bool):
                If False prevent deletion if related tracks exist,
                if True delete relationships together with the object
            remove_plugin_data (bool):
                If False prevent deletion if related plugin data exist
                if True delete plugin data together with the object
            remove_resources (bool):
                If False, keep the related resources, e.g. files
                if True, delete the related resources

        Returns:
            success (bool): True if removal was successful, False otherwise.
        """
        track_id = ensure_uuid(track_id)
        with self.session_scope() as session:
            tracks_with_relations = self._get_related_tracks_query(
                track_id=track_id,
                session=session,
                direction="both",
                user_id=uuid.UUID(user_id) if user_id is not None else None,
            ).all()
            collections_with_relations = (
                session.query(model.NendoCollectionDB)
                .join(
                    model.TrackCollectionRelationshipDB,
                    model.NendoCollectionDB.id
                    == model.TrackCollectionRelationshipDB.target_id,
                )
                .filter(model.TrackCollectionRelationshipDB.source_id == track_id)
                .all()
            )
            user_id = self._ensure_user_uuid(user_id)
            related_plugin_data = self._get_plugin_data_db(
                track_id=track_id,
                user_id=user_id,
                session=session,
            )
            if len(related_plugin_data) > 0:
                if remove_plugin_data:
                    logger.info("Removing %d plugin data", len(related_plugin_data))
                    session.query(model.NendoPluginDataDB).filter(
                        model.NendoPluginDataDB.track_id == track_id,
                    ).delete()
                    session.commit()
                else:
                    logger.warning(
                        "Cannot remove due to %d existing "
                        "plugin data entries. Set `remove_plugin_data=True` "
                        "to remove them.",
                        len(related_plugin_data),
                    )
                    return False
            n_rel = len(tracks_with_relations) + len(collections_with_relations)
            if n_rel > 0:
                if remove_relationships:
                    session.query(model.TrackTrackRelationshipDB).filter(
                        model.TrackTrackRelationshipDB.target_id == track_id,
                    ).delete()
                    session.query(model.TrackTrackRelationshipDB).filter(
                        model.TrackTrackRelationshipDB.source_id == track_id,
                    ).delete()
                    # remove track from all collections
                    for collection in collections_with_relations:
                        self._remove_track_from_collection_db(
                            track_id=track_id,
                            collection_id=collection.id,
                            session=session,
                        )
                    session.commit()
                else:
                    logger.warning(
                        "Cannot remove due to %s existing relationships. "
                        "Set `remove_relationships=True` to remove them.",
                        n_rel,
                    )
                    return False
            # delete actual target
            target = (
                session.query(model.NendoTrackDB)
                .filter(model.NendoTrackDB.id == track_id)
                .one_or_none()
            )
            target_track = schema.NendoTrack.model_validate(target)
            session.delete(target)
        # only delete if file has been copied to the library
        # ("original_filepath" is present)
        user_id = self._ensure_user_uuid(user_id)
        if remove_resources and target_track.resource.location != "original":
            logger.info("Removing resources associated with Track %s", str(track_id))
            return self.storage_driver.remove_file(
                file_name=target_track.resource.file_name,
                user_id=str(user_id),
            )
        return True

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
        track = self.get_track(track_id=track_id)
        # Check if file_path is a directory
        if os.path.isdir(file_path):
            # Generate a filename with timestamp
            if track.has_meta("original_filename"):
                original_filename = track.get_meta("original_filename")
            else:
                original_filename = track.resource.file_name
            file_name = (
                f"{original_filename}_nendo_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"  # noqa: DTZ005
                f".{file_format}"
            )
            file_path = os.path.join(file_path, file_name)
        else:
            # Deduce file format from file extension
            file_format = os.path.splitext(file_path)[1].lstrip(".")

        # Exporting the audio
        temp_path = None
        signal = track.signal
        signal = np.transpose(signal) if signal.shape[0] <= 2 else signal
        if file_format in ("wav", "ogg"):
            sf.write(file_path, signal, track.sr, format=file_format)
        elif file_format == "mp3":
            # Create a temporary WAV file for conversion
            temp_path = file_path.rsplit(".", 1)[0] + ".wav"
            sf.write(temp_path, signal, track.sr)
            subprocess.run(
                ["ffmpeg", "-i", temp_path, "-acodec", "libmp3lame", file_path],
                check=False,
            )
        else:
            raise ValueError(
                "Unsupported file format. "
                "Supported formats are 'wav', 'mp3', and 'ogg'.",
            )

        # Clean up temporary file if used
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return file_path

    # ===============================
    #
    # COLLECTION MANAGEMENT FUNCTIONS
    #
    # ===============================

    @schema.NendoPlugin.stream_output
    def _get_collections_db(
        self,
        query: Optional[Query] = None,
        user_id: Optional[uuid.UUID] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Union[List, Iterator]:
        """Get a list of collections from the DB."""
        s = session or self.session_scope()
        with s as session_local:
            if query:
                query_local = query
            else:
                query_local = session_local.query(model.NendoCollectionDB)
                if user_id is not None:
                    query_local = query_local.filter(
                        model.NendoCollectionDB.user_id == user_id,
                    )

            query_local = query_local.options(noload("*"))

            if order_by:
                if order_by == "random":
                    query_local = query_local.order_by(func.random())
                elif order == "desc":
                    query_local = query_local.order_by(desc(order_by))
                else:
                    query_local = query_local.order_by(asc(order_by))

            if limit:
                query_local = query_local.limit(limit)
                if offset:
                    query_local = query_local.offset(offset)

            if self.config.stream_chunk_size > 1:
                chunk = []
                for collection in query_local:
                    chunk.append(schema.NendoCollection.model_validate(collection))
                    if len(chunk) == self.config.stream_chunk_size:
                        yield chunk
                        chunk = []
                if chunk:  # yield remaining tracks in non-full chunk
                    yield chunk
            else:
                for collection in query_local:
                    yield schema.NendoCollection.model_validate(collection)

    def _get_related_collections_query(
        self,
        collection_id: uuid.UUID,
        session: Session,
        direction: str = "to",
        user_id: Optional[uuid.UUID] = None,
    ) -> Query:
        """Create a query for the collections related to a given collection.

        Args:
            collection_id (UUID): ID of the collection to be searched for.
            direction (str, optional): The relationship direction
                Can be either one of "to", "from", or "both". Defaults to "to".
            session (Session): Session to be used for the transaction.
            user_id (UUID, optional): The user ID to filter for.

        Returns:
            Query: The SQLAlchemy query object.
        """
        query = session.query(model.NendoCollectionDB)
        if user_id is not None:
            query = query.filter(model.NendoCollectionDB.user_id == user_id)
        mccr = model.CollectionCollectionRelationshipDB
        if direction == "to":
            query = query.join(
                mccr,
                model.NendoCollectionDB.id == mccr.source_id,
            ).filter(
                mccr.target_id == collection_id,
            )
        elif direction == "from":
            query = query.join(
                mccr,
                model.NendoCollectionDB.id == mccr.target_id,
            ).filter(
                mccr.source_id == collection_id,
            )
        elif direction == "both":
            query = query.join(
                mccr,
                or_(
                    model.NendoCollectionDB.id == mccr.source_id,
                    model.NendoCollectionDB.id == mccr.target_id,
                ),
            ).filter(
                and_(
                    model.NendoCollectionDB.id != collection_id,
                    or_(
                        mccr.source_id == collection_id,
                        mccr.target_id == collection_id,
                    ),
                ),
            )
        else:
            raise ValueError(
                "Invalid direction value. Must be 'to', 'from', or 'both'.",
            )
        return query

    def _remove_track_from_collection_db(
        self,
        track_id: uuid.UUID,
        collection_id: uuid.UUID,
        session: Session,
    ) -> bool:
        """Deletes a relationship from the track to the collection in the db.

        Args:
            collection_id (uuid.UUID): Collection id.
            track_id (uuid.UUID): Track id.
            session (sqlalchemy.Session): Session object

        Returns:
            success (bool): True if removal was successful, False otherwise.
        """
        target_relationship = (
            session.query(model.TrackCollectionRelationshipDB)
            .filter(
                and_(
                    model.TrackCollectionRelationshipDB.source_id == track_id,
                    model.TrackCollectionRelationshipDB.target_id == collection_id,
                ),
            )
            .first()
        )
        if target_relationship is None:
            raise schema.NendoRelationshipNotFoundError(
                "Relationship not found",
                track_id,
                collection_id,
            )
        session.delete(target_relationship)
        # Adjust positions of other states
        rel_db = model.TrackCollectionRelationshipDB
        session.query(model.TrackCollectionRelationshipDB).filter(
            rel_db.target_id == collection_id,
            rel_db.relationship_position > target_relationship.relationship_position,
        ).update({rel_db.relationship_position: rel_db.relationship_position - 1})

    def add_collection(
        self,
        name: str,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        track_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        description: str = "",
        collection_type: str = "collection",
        visibility: schema.Visibility = schema.Visibility.private,
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoCollection:
        """Creates a new collection and saves it into the DB.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids
                to be added to the collection.
            name (str): Name of the collection.
            user_id (UUID, optional): The ID of the user adding the collection.
            description (str): Description of the collection.
            collection_type (str): Type of the collection.
            meta (Dict[str, Any]): Metadata of the collection.

        Returns:
            NendoCollection: The newly created NendoCollection object.
        """
        user_id = self._ensure_user_uuid(user_id)
        if track_ids is None:
            track_ids = []
        with self.session_scope() as session:
            # Fetch the track objects
            track_objs = session.query(model.NendoTrackDB).filter(
                model.NendoTrackDB.id.in_(
                    [uuid.UUID(t) if isinstance(t, str) else t for t in track_ids],
                ),
            )
            if user_id is not None:
                track_objs = track_objs.filter(model.NendoTrackDB.user_id == user_id)
            track_objs = track_objs.all()
            # Create a new collection object
            new_collection = model.NendoCollectionDB(
                name=name,
                user_id=user_id,
                description=description,
                collection_type=collection_type,
                visibility=visibility,
                meta=meta or {},
            )
            session.add(new_collection)
            session.commit()
            session.refresh(new_collection)
            # Create relationships from tracks to collection
            for idx, track in enumerate(track_objs):
                tc_relationship = model.TrackCollectionRelationshipDB(
                    source_id=track.id,
                    target_id=new_collection.id,
                    relationship_type="track",
                    meta={},
                    relationship_position=idx,
                )
                session.add(tc_relationship)
            session.commit()
            session.refresh(new_collection)

            return schema.NendoCollection.model_validate(new_collection)

    def add_related_collection(
        self,
        track_ids: List[Union[str, uuid.UUID]],
        collection_id: Union[str, uuid.UUID],
        name: str,
        description: str = "",
        user_id: Optional[Union[str, uuid.UUID]] = None,
        relationship_type: str = "relationship",
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoCollection:
        """Adds a new collection with a relationship to the given collection.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids.
            collection_id (Union[str, uuid.UUID]): Existing collection id.
            name (str): Name of the new related collection.
            description (str): Description of the new related collection.
            user_id (UUID, optional): The ID of the user adding the collection.
            relationship_type (str): Type of the relationship.
            meta (Dict[str, Any]): Meta of the new related collection.

        Returns:
            NendoCollection: The newly added NendoCollection object.
        """
        user_id = self._ensure_user_uuid(user_id)
        # Create a new collection
        new_collection = self.add_collection(
            name=name,
            user_id=user_id,
            track_ids=track_ids,
            description=description,
            collection_type=relationship_type,
            meta=meta,
        )

        with self.session_scope() as session:
            if isinstance(collection_id, str):
                collection_id = uuid.UUID(collection_id)
            collection = (
                session.query(model.NendoCollectionDB)
                .filter_by(id=collection_id)
                .first()
            )

            # Check if the collection does not exist
            if not collection:
                raise schema.NendoCollectionNotFoundError(
                    "Collection not found",
                    id=collection_id,
                )

            relationship = schema.NendoRelationshipCreate(
                source_id=new_collection.id,
                target_id=collection_id,
                relationship_type=relationship_type,
                meta=meta or {},
            )
            relationship = model.CollectionCollectionRelationshipDB(
                **relationship.model_dump(),
            )
            session.add(relationship)
        return new_collection

    def add_track_to_collection(
        self,
        track_id: Union[str, uuid.UUID],
        collection_id: Union[str, uuid.UUID],
        position: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoCollection:
        """Creates a relationship from the track to the collection.

        Args:
            track_id (Union[str, uuid.UUID]): ID of the track to add.
            collection_id (Union[str, uuid.UUID]): ID of the collection to
                which to add the track.
            position (int, optional): Target position of the track inside
                the collection.
            meta (Dict[str, Any]): Metadata of the relationship.

        Returns:
            NendoCollection: The updated NendoCollection object.
        """
        with self.session_scope() as session:
            # Convert IDs to UUIDs if they're strings
            collection_id = ensure_uuid(collection_id)
            track_id = ensure_uuid(track_id)

            # Check the collection and track objects
            collection = (
                session.query(model.NendoCollectionDB)
                .filter_by(id=collection_id)
                .first()
            )
            track = session.query(model.NendoTrackDB).filter_by(id=track_id).first()
            if not collection:
                raise schema.NendoCollectionNotFoundError(
                    "The collection does not exist",
                    collection_id,
                )
            if not track:
                raise schema.NendoCollectionNotFoundError(
                    "The track does not exist",
                    track_id,
                )

            rc_rel_db = model.TrackCollectionRelationshipDB
            if position is not None:
                # Update other states to keep ordering consistent
                session.query(rc_rel_db).filter(
                    rc_rel_db.target_id == collection_id,
                    rc_rel_db.relationship_position >= position,
                ).update(
                    {
                        rc_rel_db.relationship_position: rc_rel_db.relationship_position
                        + 1,
                    },
                )
            else:
                # If no position specified, add at the end
                last_state = (
                    session.query(model.TrackCollectionRelationshipDB)
                    .filter_by(target_id=collection_id)
                    .order_by(
                        model.TrackCollectionRelationshipDB.relationship_position.desc(),
                    )
                    .first()
                )
                position = last_state.relationship_position + 1 if last_state else 0

            # Create a relationship from the track to the collection
            tc_relationship = model.TrackCollectionRelationshipDB(
                source_id=track_id,
                target_id=collection_id,
                relationship_type="track",
                meta=meta or {},
                relationship_position=position,
            )
            session.add(tc_relationship)
            session.commit()
            session.refresh(collection)
            return schema.NendoCollection.model_validate(collection)

    def add_tracks_to_collection(
        self,
        track_ids: List[Union[str, uuid.UUID]],
        collection_id: Union[str, uuid.UUID],
        meta: Optional[Dict[str, Any]] = None,
    ) -> schema.NendoCollection:
        """Creates a relationship from the track to the collection.

        Args:
            track_ids (List[Union[str, uuid.UUID]]): List of track ids to add.
            collection_id (Union[str, uuid.UUID]): ID of the collection to
                which to add the track.
            meta (Dict[str, Any], optional): Metadata of the relationship.

        Returns:
            NendoCollection: The updated NendoCollection object.
        """
        with self.session_scope() as session:
            # Convert IDs to UUIDs if they're strings
            collection_id = ensure_uuid(collection_id)
            track_ids = [ensure_uuid(track_id) for track_id in track_ids]

            # Check the collection and track objects
            collection = (
                session.query(model.NendoCollectionDB)
                .filter_by(id=collection_id)
                .first()
            )
            if not collection:
                raise schema.NendoCollectionNotFoundError(
                    "The collection does not exist",
                    collection_id,
                )
            existing_track_ids = (
                session.query(model.NendoTrackDB)
                .filter(model.NendoTrackDB.id.in_(track_ids))
                .all()
            )
            existing_track_ids = [t.id for t in existing_track_ids]
            missing_ids = [tid for tid in track_ids if tid not in existing_track_ids]
            if len(missing_ids) > 0:
                raise schema.NendoCollectionNotFoundError(
                    "Tracks do not exist: ",
                    missing_ids,
                )

            # append all tracks to the end of the collection
            last_postition = (
                session.query(model.TrackCollectionRelationshipDB)
                .filter_by(target_id=collection_id)
                .order_by(
                    model.TrackCollectionRelationshipDB.relationship_position.desc(),
                )
                .first()
            )
            position = last_postition.relationship_position + 1 if last_postition else 0

            # create relationships from all tracks to the collection
            for track_id in track_ids:
                tc_relationship = model.TrackCollectionRelationshipDB(
                    source_id=track_id,
                    target_id=collection_id,
                    relationship_type="track",
                    meta=meta or {},
                    relationship_position=position,
                )
                session.add(tc_relationship)
                position += 1
            session.commit()
            session.refresh(collection)
            return schema.NendoCollection.model_validate(collection)

    def get_collection_tracks(
        self,
        collection_id: uuid.UUID,
        order: Optional[str] = "asc",
    ) -> List[schema.NendoTrack]:
        """Get all tracks from a collection.

        Args:
            collection_id (Union[str, uuid.UUID]): ID of the collection from which to
                get all tracks.
            order (str, optional): Ordering direction. Defaults to "asc".

        Returns:
            List[NendoTrack]: List of tracks in the collection.
        """
        with self.session_scope() as session:
            tracks_db = (
                session.query(model.NendoTrackDB).join(
                    model.TrackCollectionRelationshipDB,
                    model.TrackCollectionRelationshipDB.source_id
                    == model.NendoTrackDB.id,
                )
                # .options(joinedload(model.NendoTrackDB.related_collections))
                .filter(model.TrackCollectionRelationshipDB.target_id == collection_id)
            )
            if order:
                if order == "random":
                    tracks_db = tracks_db.order_by(func.random())
                elif order == "desc":
                    tracks_db = tracks_db.order_by(
                        desc(
                            model.TrackCollectionRelationshipDB.relationship_position,
                        ),
                    )
                else:
                    tracks_db = tracks_db.order_by(
                        asc(
                            model.TrackCollectionRelationshipDB.relationship_position,
                        ),
                    )

            tracks_db = tracks_db.all()

            return (
                [schema.NendoTrack.model_validate(t) for t in tracks_db]
                if tracks_db is not None
                else None
            )

    def get_collection(
        self,
        collection_id: uuid.UUID,
        get_related_tracks: bool = True,
    ) -> schema.NendoCollection:
        """Get a collection by its ID.

        Args:
            collection_id (uuid.UUID): ID of the target collection.
            get_related_tracks (bool, optional): Flag that defines whether the
                returned collection should contain the `related_tracks`.
                Defaults to True.

        Returns:
            NendoCollection: The collection object.
        """
        with self.session_scope() as session:
            query = session.query(model.NendoCollectionDB)
            if get_related_tracks:
                query = query.options(
                    joinedload(model.NendoCollectionDB.related_tracks).joinedload(
                        model.TrackCollectionRelationshipDB.source,
                    ),
                )
            else:
                query = query.options(
                    noload(model.NendoCollectionDB.related_tracks),
                )
            collection_db = query.filter(
                model.NendoCollectionDB.id == collection_id,
            ).first()

            return (
                schema.NendoCollection.model_validate(collection_db)
                if collection_db is not None
                else None
            )

    def get_collections(
        self,
        query: Optional[Query] = None,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Union[List, Iterator]:
        """Get a list of collections.

        Args:
            query (Query, optional): Query object to build from.
            user_id (Union[str, UUID], optional): The user ID to filter for.
            order_by (str, optional): Key used for ordering the results.
            order (str, optional): Order in which to retrieve results
                ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results (requires limit).
            session (sqlalchemy.Session): Session object to commit to.

        Returns:
            Union[List, Iterator]: List or generator of collections, depending on the
                configuration variable stream_mode
        """
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = session.query(model.NendoCollectionDB)
            if user_id is not None:
                query = query.filter(model.NendoCollectionDB.user_id == user_id)
            return self._get_collections_db(
                query,
                user_id,
                order_by,
                order,
                limit,
                offset,
                session,
            )

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
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = session.query(model.NendoCollectionDB)
            if value is not None and len(value) > 0:
                query = query.filter(
                    and_(
                        or_(
                            model.NendoCollectionDB.name.ilike(f"%{value}%"),
                            model.NendoCollectionDB.description.ilike(f"%{value}%"),
                            # cast(
                            #     model.NendoCollectionDB.meta, Text()).ilike(f"%{value}%"
                            # ),
                        ),
                    ),
                )
            if user_id is not None:
                query = query.filter(model.NendoCollectionDB.user_id == user_id)
            if collection_types is not None:
                query = query.filter(
                    model.NendoCollectionDB.collection_type.in_(collection_types),
                )
            return self._get_collections_db(
                query,
                user_id,
                order_by,
                order,
                limit,
                offset,
                session,
            )

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
            order (str, optional): Order in which to retrieve results
                ("asc" or "desc").
            limit (int, optional): Limit the number of returned results.
            offset (int, optional): Offset into the paginated results
                (requires limit).

        Returns:
            Union[List, Iterator]: List or generator of collections, depending on the
                configuration variable stream_mode
        """
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = self._get_related_collections_query(
                collection_id=ensure_uuid(collection_id),
                session=session,
                direction=direction,
                user_id=user_id,
            )
            return self._get_collections_db(
                query,
                order_by,
                order,
                limit,
                offset,
                session,
            )

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
        collection_id = ensure_uuid(collection_id)
        with self.session_scope() as session:
            return (
                session.query(model.NendoTrackDB)
                .join(
                    model.TrackCollectionRelationshipDB,
                    model.TrackCollectionRelationshipDB.source_id
                    == model.NendoTrackDB.id,
                )
                .filter(model.TrackCollectionRelationshipDB.target_id == collection_id)
                .count()
            )

    def remove_track_from_collection(
        self,
        track_id: Union[str, uuid.UUID],
        collection_id: Union[str, uuid.UUID],
    ) -> bool:
        """Deletes a relationship from the track to the collection.

        Args:
            track_id (Union[str, uuid.UUID]): ID
            collection_id (Union[str, uuid.UUID]): Collection id.

        Returns:
            success (bool): True if removal was successful, False otherwise.
        """
        with self.session_scope() as session:
            collection_id = ensure_uuid(collection_id)
            track_id = ensure_uuid(track_id)

            # # Check the collection and track objects
            # collection = (
            #     session.query(model.NendoCollectionDB)
            #     .filter_by(id=collection_id)
            #     .first()
            # )
            # track = session.query(model.NendoTrackDB).filter_by(id=track_id).first()
            # if not collection:
            #     raise ValueError("The collection does not exist")
            # if not track:
            #     raise ValueError("The track does not exist")

            # Remove the relationship from the track to the collection
            return self._remove_track_from_collection_db(
                track_id=track_id,
                collection_id=collection_id,
                session=session,
            )

    def update_collection(
        self,
        collection: schema.NendoCollection,
    ) -> schema.NendoCollection:
        """Updates the given collection by storing it to the database.

        Args:
            collection (NendoCollection): The collection to store.

        Raises:
            NendoCollectionNotFoundError: If the collection with
                the given ID was not found.

        Returns:
            NendoCollection: The updated collection.
        """
        with self.session_scope() as session:
            collection_db = (
                session.query(model.NendoCollectionDB)
                .filter_by(id=collection.id)
                .first()
            )

            if collection_db is None:
                raise schema.NendoCollectionNotFoundError(
                    "Collection not found",
                    collection.id,
                )

            collection_db.name = collection.name
            collection_db.user_id = collection.user_id
            collection_db.description = collection.description
            collection_db.collection_type = collection.collection_type
            collection_db.visibility = collection.visibility
            collection_db.meta = collection.meta

            session.commit()
            session.refresh(collection_db)
            return schema.NendoCollection.model_validate(collection_db)

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
        with self.session_scope() as session:
            # has_related_track = (
            #     session.query(model.TrackCollectionRelationshipDB)
            #     .filter(
            #         model.TrackCollectionRelationshipDB.target_id
            #         == collection_id
            #     )
            #     .first()
            # ) is not False
            has_related_collection = (
                session.query(model.CollectionCollectionRelationshipDB)
                .filter(
                    or_(
                        model.CollectionCollectionRelationshipDB.source_id
                        == collection_id,
                        model.CollectionCollectionRelationshipDB.target_id
                        == collection_id,
                    ),
                )
                .first()
            ) is not None

            if has_related_collection:  # or has_related_track:
                if remove_relationships:
                    session.query(model.CollectionCollectionRelationshipDB).filter(
                        or_(
                            model.CollectionCollectionRelationshipDB.target_id
                            == collection_id,
                            model.CollectionCollectionRelationshipDB.source_id
                            == collection_id,
                        ),
                    ).delete()
                    session.commit()
                else:
                    logger.warning(
                        "Cannot remove due to existing relationships. "
                        "Set `remove_relationships=True` to remove them.",
                    )
                    return False

            # clean up track-collection relationships
            session.query(model.TrackCollectionRelationshipDB).filter(
                model.TrackCollectionRelationshipDB.target_id == collection_id,
            ).delete()
            session.commit()

            # delete actual target
            query = session.query(model.NendoCollectionDB).filter(
                model.NendoCollectionDB.id == collection_id,
            )
            if user_id is not None:
                user_id = self._ensure_user_uuid(user_id)
                query = query.filter(
                    model.NendoCollectionDB.user_id == user_id,
                )
            query.delete()

        return True

    def export_collection(
        self,
        collection_id: Union[str, uuid.UUID],
        export_path: str,
        filename_suffix: str = "nendo",
        file_format: str = "wav",
    ) -> List[str]:
        """Export the collection to a directory.

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
        collection_tracks = self.get_collection_tracks(collection_id)
        now = datetime.now().strftime("%Y%m%d%H%M%S")  # noqa: DTZ005
        if not os.path.isdir(export_path):
            logger.info(
                f"Export path {export_path} does not exist, creating now.",
            )
            os.makedirs(export_path, exist_ok=True)
        track_file_paths = []
        for track in collection_tracks:
            if track.has_meta("original_filename"):
                original_filename = track.get_meta("original_filename")
            else:
                original_filename = track.resource.file_name
            file_name = f"{original_filename}_{filename_suffix}_{now}.{file_format}"
            file_path = os.path.join(export_path, file_name)
            track_file_path = self.export_track(
                track_id=track.id,
                file_path=file_path,
                file_format=file_format,
            )
            track_file_paths.append(track_file_path)
        return track_file_paths

    # =========================
    #
    # BLOB MANAGEMENT FUNCTIONS
    #
    # =========================

    def _upsert_blob_db(
        self,
        blob: schema.NendoBlobBase,
        session: Session,
    ) -> model.NendoBlobDB:
        """Create blob in DB or update if it exists.

        Args:
            blob (schema.NendoBlobCreate): Blob object to be created
            session (Session): Session to be used for the transaction

        Returns:
            model.NendoBlobDB: The ORM model object of the upserted blob
        """
        if type(blob) == schema.NendoBlobCreate:
            # create new blob
            db_blob = model.NendoBlobDB(**blob.model_dump())
            session.add(db_blob)
        else:
            # update existing blob
            db_blob = (
                session.query(model.NendoBlobDB).filter_by(id=blob.id).one_or_none()
            )
            if db_blob is None:
                raise schema.NendoBlobNotFoundError("Blob not found", target_id=blob.id)
            db_blob.resource = blob.resource.model_dump()
        session.commit()
        return db_blob

    def _create_blob_from_bytes(
        self,
        data: bytes,
        user_id: Optional[uuid.UUID] = None,
    ) -> schema.NendoBlobCreate:
        """Create a blob from the given bytes."""
        target_file = None
        user_id_str = str(user_id) if user_id else str(self.user.id)
        try:
            target_file = self.storage_driver.save_bytes(
                file_name=self.storage_driver.generate_filename(
                    filetype="pkl",
                    user_id=user_id_str,
                ),
                data=data,
                user_id=user_id_str,
            )
        except Exception as e:  # noqa: BLE001
            raise schema.NendoLibraryError(
                f"Failed writing file {target_file} to the library. Error: {e}.",
            ) from None
        resource = schema.NendoResource(
            file_path=self.storage_driver.get_file_path(
                src=target_file,
                user_id=user_id_str,
            ),
            file_name=self.storage_driver.get_file_name(
                src=target_file,
                user_id=user_id_str,
            ),
            resource_type="blob",
            location=self.storage_driver.get_driver_location(),
            meta={},
        )
        return schema.NendoBlobCreate(
            resource=resource.model_dump(),
            user_id=self.user.id,
        )

    def _create_blob_from_file(
        self,
        file_path: FilePath,
        copy_to_library: Optional[bool] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> schema.NendoBlobCreate:
        """Create a blob from a given filepath."""
        target_file = None
        if not os.path.isfile(file_path):
            raise schema.NendoResourceError("File not found", file_path)

        copy_to_library = copy_to_library or self.config.copy_to_library
        meta = {}
        meta.update({"checksum": md5sum(file_path)})
        if copy_to_library:
            try:
                file_stats = os.stat(file_path)
                meta.update(
                    {
                        "original_filename": os.path.basename(file_path),
                        "original_filepath": os.path.dirname(file_path),
                        "original_size": file_stats.st_size,
                        "original_checksum": md5sum(file_path),
                    },
                )

                target_file = self.storage_driver.save_file(
                    file_name=self.storage_driver.generate_filename(
                        filetype=os.path.splitext(file_path)[1][1:],  # without the dot
                        user_id=user_id,
                    ),
                    file_path=file_path,
                    user_id=str(user_id) if user_id else str(self.user.id),
                )
                location = self.storage_driver.get_driver_location()
            except Exception as e:  # noqa: BLE001
                raise schema.NendoLibraryError(
                    f"Failed storing blob {target_file}. Error: {e}.",
                ) from None
        else:
            target_file = file_path
            location = schema.ResourceLocation.original

        resource = schema.NendoResource(
            file_path=os.path.dirname(target_file),
            file_name=os.path.basename(target_file),
            location=location,
            meta=meta or {},
        )
        return schema.NendoBlobCreate(
            resource=resource.model_dump(),
            user_id=self.user.id,
        )

    def load_blob(
        self,
        blob_id: uuid.UUID,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> schema.NendoBlob:
        """Loads a blob of data into memory.

        Args:
            blob_id (uuid.UUID): The UUID of the blob.
            user_id Union[str, uuid.UUID], optional): ID of the user
                who's loading the blob.

        Returns:
            schema.NendoBlob: The loaded blob.
        """
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            blob_db = (
                session.query(model.NendoBlobDB)
                .filter(model.NendoBlobDB.id == blob_id)
                .one_or_none()
            )
            if blob_db is not None:
                blob = schema.NendoBlob.model_validate(blob_db)
                local_blob = self.storage_driver.as_local(
                    file_path=blob.resource.src,
                    location=blob.resource.location,
                    user_id=str(user_id),
                )

                # load blob data into memory
                if os.path.splitext(local_blob)[1] == ".pkl":
                    with open(local_blob, "rb") as f:
                        blob.data = pickle.load(f)  # noqa: S301
                elif os.path.splitext(local_blob)[1] == ".npy":
                    blob.data = np.load(local_blob)
                elif os.path.splitext(local_blob)[1] == ".wav":
                    librosa.load(local_blob, mono=False)
                else:
                    logger.error(
                        "Blob file format not recognized. "
                        "Returning blob with empty data.",
                    )

        return blob

    def store_blob(
        self,
        file_path: Union[str, FilePath],
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> schema.NendoBlob:
        """Stores a blob of data.

        Args:
            file_path (Union[str, FilePath]): The blob to store.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's storing the file to blob.

        Returns:
            schema.NendoBlob: The stored blob.
        """
        user_id = self._ensure_user_uuid(user_id)
        blob = self._create_blob_from_file(file_path=file_path, user_id=user_id)
        if blob is not None:
            with self.session_scope() as session:
                db_blob = self._upsert_blob_db(blob, session)
                blob = schema.NendoBlob.model_validate(db_blob)
        return blob

    def store_blob_from_bytes(
        self,
        data: bytes,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> schema.NendoBlob:
        """Stores a data of type `bytes` to a blob.

        Args:
            data (bytes): The blob to store.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's storing the bytes to blob.

        Returns:
            schema.NendoBlob: The stored blob.
        """
        user_id = self._ensure_user_uuid(user_id)
        blob = self._create_blob_from_bytes(data=data, user_id=user_id)
        if blob is not None:
            with self.session_scope() as session:
                db_blob = self._upsert_blob_db(blob, session)
                blob = schema.NendoBlob.model_validate(db_blob)
        return blob

    def remove_blob(
        self,
        blob_id: uuid.UUID,
        remove_resources: bool = True,
        user_id: Optional[Union[str, uuid.UUID]] = None,
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
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            target = (
                session.query(model.NendoBlobDB)
                .filter(model.NendoBlobDB.id == blob_id)
                .first()
            )
            session.delete(target)
        if remove_resources:
            logger.info("Removing resources associated with Blob %s", str(blob_id))
            try:
                self.storage_driver.remove_file(
                    file_name=target.resource["file_name"],
                    user_id=str(user_id),
                )
            except Exception as e:  # noqa: BLE001
                logger.error(
                    "Removing %s failed: %s",
                    target.resource.model_dump().src,
                    e,
                )
        return True

    # ==================================
    #
    # MISCELLANEOUS MANAGEMENT FUNCTIONS
    #
    # ==================================

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
        user_id = self._ensure_user_uuid(user_id)
        with self.session_scope() as session:
            query = session.query(model.NendoTrackDB)
            if user_id is not None:
                query = query.filter(model.NendoTrackDB.user_id == user_id)
            return query.count()

    def reset(
        self,
        force: bool = False,
        user_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> None:
        """Reset the nendo library.

        Erase all tracks, collections and relationships. Ask before erasing everything.

        Args:
            force (bool, optional): Flag that specifies whether to ask the user for
                confirmation of the operation. Default is to ask the user.
            user_id (Union[str, uuid.UUID], optional): ID of the user
                who's resetting the library. If none is given, the configured
                nendo default user will be used.
        """
        user_id = self._ensure_user_uuid(user_id)
        should_proceed = (
            force
            or input(
                "Are you sure you want to reset the library? "
                "This will purge ALL tracks, collections and relationships!"
                "Enter 'y' to confirm: ",
            ).lower()
            == "y"
        )

        if not should_proceed:
            logger.info("Reset operation cancelled.")
            return

        logger.info("Resetting nendo library.")
        with self.session_scope() as session:
            # delete all relationships
            session.query(model.TrackTrackRelationshipDB).delete()
            session.query(model.TrackCollectionRelationshipDB).delete()
            session.query(model.CollectionCollectionRelationshipDB).delete()
            # delete all plugin data
            session.query(model.NendoPluginDataDB).delete()
            session.commit()
            # delete all collections
            session.query(model.NendoCollectionDB).delete()
            # delete all tracks
            session.query(model.NendoTrackDB).delete()
        # remove files
        for library_file in self.storage_driver.list_files(user_id=str(user_id)):
            self.storage_driver.remove_file(
                file_name=library_file,
                user_id=str(user_id),
            )
