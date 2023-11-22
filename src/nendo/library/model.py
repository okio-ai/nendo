# -*- encoding: utf-8 -*-
# ruff: noqa: A003
"""Module containing all SQLAlchemy ORM models for the nendo core schema.

Used by the SQLAlchemy implementation of the nendo library.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime

import numpy as np
from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.dialects.postgresql import ENUM, JSON, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy_json import NestedMutableDict, NestedMutableList, mutable_json_type

from nendo import schema

Base = declarative_base(metadata=MetaData())


def convert(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return convert(list(obj))
    if isinstance(obj, np.float32):
        return float(obj)
    if isinstance(obj, NestedMutableList) or isinstance(obj, list):
        return [convert(x) for x in obj]
    if isinstance(obj, NestedMutableDict) or isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    return obj


class JSONEncodedDict(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value, dialect):
        return json.dumps(convert(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)


class TrackTrackRelationshipDB(Base):
    __tablename__ = "track_track_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"))
    target_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    relationship_type = Column(String)
    meta = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))

    # relationships
    source = relationship(
        "NendoTrackDB",
        foreign_keys=[source_id],
        back_populates="related_tracks",
    )
    target = relationship("NendoTrackDB", foreign_keys=[target_id])


class TrackCollectionRelationshipDB(Base):
    __tablename__ = "track_collection_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"))
    target_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    relationship_type = Column(String)
    meta = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))
    relationship_position = Column(Integer, nullable=False)

    # relationships
    source = relationship("NendoTrackDB", foreign_keys=[source_id])
    target = relationship("NendoCollectionDB", foreign_keys=[target_id])


class CollectionCollectionRelationshipDB(Base):
    __tablename__ = "collection_collection_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    target_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    relationship_type = Column(String)
    meta = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))

    # relationships
    source = relationship("NendoCollectionDB", foreign_keys=[source_id])
    target = relationship("NendoCollectionDB", foreign_keys=[target_id])


class NendoPluginDataDB(Base):
    __tablename__ = "plugin_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    track_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"))
    user_id = Column(UUID(as_uuid=True))  # , ForeignKey("users.id"))
    plugin_name = Column(String, nullable=False)
    plugin_version = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # relationships
    # track = relationship("NendoTrackDB", backref="plugin_data")


class NendoTrackDB(Base):
    __tablename__ = "tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    track_type = Column(String, default="track")
    visibility = Column(ENUM(schema.Visibility), default="private")
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), default=func.now())
    images = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))
    resource = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))
    meta = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))

    # Relationships
    related_tracks = relationship(
        "TrackTrackRelationshipDB",
        primaryjoin="NendoTrackDB.id==TrackTrackRelationshipDB.source_id",
        foreign_keys="[TrackTrackRelationshipDB.source_id]",
        back_populates="source",
        # cascade="all, delete-orphan",
    )
    related_collections = relationship(
        "TrackCollectionRelationshipDB",
        primaryjoin="NendoTrackDB.id==TrackCollectionRelationshipDB.source_id",
        foreign_keys="[TrackCollectionRelationshipDB.source_id]",
        back_populates="source",
        # cascade="all, delete-orphan",
    )
    plugin_data = relationship(
        "NendoPluginDataDB",
        primaryjoin="NendoTrackDB.id==NendoPluginDataDB.track_id",
        foreign_keys="[NendoPluginDataDB.track_id]",
        # cascade="all, delete-orphan",
    )


class NendoBlobDB(Base):
    __tablename__ = "blobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    visibility = Column(ENUM(schema.Visibility), default="private")
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
    )
    created_at = Column(DateTime(timezone=True), default=func.now())
    resource = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))


class NendoCollectionDB(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    user_id = Column(UUID(as_uuid=True))
    description = Column(Text, default="")
    collection_type = Column(String, default="generic")
    visibility = Column(ENUM(schema.Visibility), default="private")
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
    )
    created_at = Column(DateTime(timezone=True), default=func.now())
    meta = Column(mutable_json_type(dbtype=JSONEncodedDict, nested=True))

    # relationships
    related_tracks = relationship(
        "TrackCollectionRelationshipDB",
        primaryjoin="NendoCollectionDB.id==TrackCollectionRelationshipDB.target_id",
        foreign_keys="[TrackCollectionRelationshipDB.target_id]",
        back_populates="target",
        # cascade="all, delete-orphan",
    )

    related_collections = relationship(
        "CollectionCollectionRelationshipDB",
        primaryjoin="NendoCollectionDB.id==CollectionCollectionRelationshipDB.source_id",
        foreign_keys="[CollectionCollectionRelationshipDB.source_id]",
        back_populates="source",
        # cascade="all, delete-orphan",
    )
