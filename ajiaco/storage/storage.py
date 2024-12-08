from dataclasses import dataclass, field
import peewee as pw
from playhouse import db_url

from . import models

_BASE_MODELS = (
    models.Session,
    models.Subject,
    models.Round,
    models.Group,
    models.Role,
    models.StageHistory,
)


@dataclass(frozen=True)
class Storage:

    database: pw.Database
    _models: list = field(init=False, default_factory=list, repr=False)

    def __post_init__(self):
        for basemodel in _BASE_MODELS:

            class Meta:
                table_name = basemodel._meta.table_name
                database = self.database

            name = basemodel.__name__
            Model = type(name, (basemodel,), {"Meta": Meta})
            self._models.append(Model)

    @classmethod
    def from_url(cls, url):
        db = db_url.connect(url)
        return cls(database=db)

    @property
    def models(self):
        return tuple(self._models)

    def create_tables(self):
        with self.database:
            self.database.create_tables(self._models)
