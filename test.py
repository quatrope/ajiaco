from ajiaco import storage


stg = storage.Storage.from_url("sqlite:///coso.sqlite")


with stg.transaction() as ses:
    ses.create_tables()
