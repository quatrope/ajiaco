import inspect
from dataclasses import dataclass, field

import peewee as pw
from playhouse import db_url, signals

from . import models

_BASE_MODELS = (
    models.Session,
    models.Subject,
    models.Round,
    models.Group,
    models.Role,
    models.StageHistory,
)

_SIGNALS = {
    "pre_save": signals.pre_save,
    "post_save": signals.post_save,
    "pre_delete": signals.pre_delete,
    "post_delete": signals.post_delete,
    "pre_init": signals.pre_init,
}


@dataclass(frozen=True)
class _Session:
    transaction: ...
    models: ...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def create_tables(self, **options):
        database = self.transaction.db
        models = self.models
        database.create_tables(models, **options)


@dataclass(frozen=True)
class Storage:

    database: pw.Database
    models: list = field(init=False, default_factory=list, repr=False)

    def __post_init__(self):
        for basemodel in _BASE_MODELS:

            class Meta:
                table_name = basemodel._meta.table_name
                database = self.database

            name = basemodel.__name__

            Model = type(name, (basemodel,), {"Meta": Meta})

            for signal_name, signal in _SIGNALS.items():
                handler = getattr(Model, signal_name, None)
                if handler and inspect.ismethod(handler):
                    signal.connect(handler, sender=Model)

            self.models.append(Model)

    @classmethod
    def from_url(cls, url):
        db = db_url.connect(url)
        return cls(database=db)

    def transaction(self):
        with self.database.atomic() as txn:
            return _Session(transaction=txn, models=self.models)
