import attrs

import sqlalchemy as sa
from sqlalchemy import orm

import sqlalchemy_utils as sa_utils

from .models import ModelsContainer, create_models


class StorageSession(orm.Session):

    def __init__(self, storage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage


@attrs.define(frozen=True)
class Storage:

    engine: sa.Engine
    metadata: sa.MetaData = attrs.field(
        init=False,
        factory=sa.MetaData,
        repr=False,
    )
    session_maker: orm.Session = attrs.field(init=False, repr=False)
    models: ModelsContainer = attrs.field(init=False, repr=False)

    @session_maker.default
    def _session_maker_default(self):
        maker = orm.sessionmaker(
            bind=self.engine,
            class_=StorageSession,
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
        return self.session_maker()

    def stamp(self):
        pass
