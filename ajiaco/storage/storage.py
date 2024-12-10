from dataclasses import dataclass, field

import peewee as pw
from playhouse import db_url

from . import models


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
    models: set = field(init=False, default_factory=set, repr=False)

    def __post_init__(self):
        the_models = models.create_models(self.database)
        self.models.update(the_models)

    @classmethod
    def from_url(cls, url):
        db = db_url.connect(url)
        return cls(database=db)

    def transaction(self):
        with self.database.atomic() as txn:
            return _Session(transaction=txn, models=self.models)
