# -*- encoding: utf-8 -*-
"""Module implementing the NendoLibraryPlugin using DuckDB.

A lightweight and fast implementation that is used as
Nendo's default library implementation.
"""

import logging
from typing import Any, Optional

from requests import Session
from sqlalchemy import Engine, create_engine

from nendo import schema
from nendo.config import NendoConfig, get_settings
from nendo.library import model
from nendo.utils import play_signal

from .sqlalchemy_library import SqlAlchemyNendoLibrary

logger = logging.getLogger("nendo")


class DuckDBLibrary(SqlAlchemyNendoLibrary):
    """DuckDB-based implementation of the Nendo Library.

    Inherits almost all functions from the SQLAlchemy implementation of the
    `NendoLibraryPlugin` and only differs in the way it connects to the database.
    """

    config: NendoConfig = None
    user: schema.NendoUser = None
    db: Engine = None
    storage_driver: schema.NendoStorage = None

    def __init__(
        self,
        config: Optional[NendoConfig] = None,
        db: Optional[Engine] = None,
        session: Optional[Session] = None,
        **kwargs: Any,
    ) -> None:
        """Configure and connect to the database."""
        super().__init__(**kwargs)
        self.config = config or get_settings()

        if self.storage_driver is None:
            self.storage_driver = schema.NendoStorageLocalFS(
                library_path=self.config.library_path, user_id=self.config.user_id,
            )

        self._connect(db, session)

    def _connect(
        self,
        db: Optional[Engine] = None,
        session: Optional[Session] = None,  # noqa: ARG002
    ) -> None:
        """Open local DuckDB session."""
        self.db = db or create_engine(f"duckdb:///{self.config.library_path}/nendo.db")
        model.Base.metadata.create_all(bind=self.db)
        self.user = self.default_user

    def play(self, track: schema.NendoTrack) -> None:
        """Preview an audio track on mac & linux.

        Args:
            track (NendoTrack): The track to play.
        """
        play_signal(track.signal, track.sr)
