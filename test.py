from ajiaco import storage

url = "firebird+firebird://sysdba:masterkey@localhost///home/juanbc/proyectos/ajiaco/src/my_project.fdb"

stg = storage.AjcStorage.from_url(url)

import ipdb; ipdb.set_trace()
with stg.transaction() as ses:
    ses.create_tables()
