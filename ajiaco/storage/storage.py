import contextlib

import attrs

import sqlalchemy as sa
from sqlalchemy import orm

import sqlalchemy_utils as sa_utils

from .models import AjcModelsContainer, create_models


class AjcStorageSession(orm.Session):
    def __init__(self, storage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage

    @property
    def models(self):
        return self.storage.models

    def get_stamp(self):
        stamp = self.query(self.models.Stamp).first()
        return stamp.data if stamp else None

    def stamp(self, data):
        Stamp = self.models.Stamp
        if self.get_stamp() is not None:
            raise ValueError("Database already stamped")
        stamp = Stamp(data=data)
        self.add(stamp)


class AjcTransactionConectManager(contextlib.AbstractContextManager):
    """Provide a transactional scope around a series of operations."""

    def __init__(self, session_maker):
        self._session_maker = session_maker

    def __enter__(self):
        self._session = self._session_maker()
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()


@attrs.define(frozen=True)
class AjcStorage:

    engine: sa.Engine
    metadata: sa.MetaData = attrs.field(
        init=False,
        factory=sa.MetaData,
        repr=False,
    )
    session_maker: orm.Session = attrs.field(init=False, repr=False)
    models: AjcModelsContainer = attrs.field(init=False, repr=False)

    @session_maker.default
    def _session_maker_default(self):
        maker = orm.sessionmaker(
            bind=self.engine,
            class_=AjcStorageSession,
            storage=self,
        )
        return maker

    @models.default
    def _models_default(self) -> set:
        return create_models(metadata=self.metadata)

    # OTHER CONSTRUCTORS ======================================================

    @classmethod
    def from_url(cls, db_url, **kwargs):
        kwargs.setdefault("echo", False)
        the_engine = sa.create_engine(db_url, **kwargs)
        return cls(engine=the_engine)

    # API =====================================================================

    def exists(self):
        return sa_utils.functions.database_exists(self.engine.url)

    def drop_storage(self):
        return sa_utils.functions.drop_database(self.engine.url)

    def create_storage(self):
        return sa_utils.functions.create_database(self.engine.url)

    def create_schema(self):
        BaseModel = self.models.BaseModel
        return BaseModel.metadata.create_all(self.engine)

    def transaction(self):
        return AjcTransactionConectManager(self.session_maker)
