from ajiaco import storage


stg = storage.Storage.from_url("sqlite:///coso.sqlite")

with stg.transaction() as ses:
    import ipdb; ipdb.set_trace()
    ses.create_tables()