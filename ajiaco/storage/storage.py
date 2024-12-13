import attrs

import sqlalchemy as sa
from sqlalchemy import orm


from . import models


class _StorageSession(orm.Session):

    def __init__(self, storage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage

    def create_tables(self):
        BaseModel = self.storage.models.BaseModel
        return BaseModel.metadata.create_all(self.bind)


@attrs.define(frozen=True)
class Storage:

    engine: sa.Engine
    metadata: sa.MetaData = attrs.field(
        init=False,
        factory=sa.MetaData,
        repr=False,
    )
    session_maker: orm.Session = attrs.field(init=False, repr=False)
    models: ... = attrs.field(init=False, repr=False)

    @session_maker.default
    def _session_maker_default(self):
        maker = orm.sessionmaker(
            bind=self.engine,
            class_=_StorageSession,
            storage=self,
        )
        return maker

    @models.default
    def _models_default(self) -> set:
        return models.create_models(metadata=self.metadata)

    # OTHER CONSTRUCTORS ======================================================

    @classmethod
    def from_url(cls, dburl, **kwargs):
        kwargs.setdefault("echo", False)
        the_engine = sa.create_engine(dburl, **kwargs)
        return cls(engine=the_engine)

    # API =====================================================================

    def transaction(self):
        return self.session_maker()
