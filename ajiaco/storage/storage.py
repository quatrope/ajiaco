from dataclasses import dataclass, field

import sqlalchemy as sa
from sqlalchemy import orm


from . import models


class _AJCSession(orm.Session):

    def __init__(self, storage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage

    def create_tables(self):
        BaseModel = self.storage.BaseModel
        return BaseModel.metadata.create_all(self.bind)


def _default_session_maker():
    return orm.sessionmaker(class_=_AJCSession)


@dataclass(frozen=True)
class Storage:

    engine: sa.Engine
    BaseModel: orm.DeclarativeBase = field(
        init=False,
        default_factory=orm.declarative_base,
        repr=False,
    )
    session_maker: orm.Session = field(
        init=False,
        default_factory=_default_session_maker,
        repr=False,
    )
    models: set = field(
        init=False,
        default_factory=set,
        repr=False,
    )

    def __post_init__(self):
        the_models = models.create_models(base_model_cls=self.BaseModel)
        self.models.update(the_models)

        self.session_maker.configure(bind=self.engine, storage=self)

    @classmethod
    def from_url(cls, dburl, echo=False):
        the_engine = sa.create_engine(dburl, echo=echo)
        return cls(engine=the_engine)

    def transaction(self):
        return self.session_maker()
