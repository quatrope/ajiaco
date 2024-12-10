from ajiaco import storage


stg = storage.Storage.from_url("sqlite:///coso.sqlite")
stg.create_tables()