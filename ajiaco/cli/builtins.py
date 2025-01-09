from .register import AjcCommandRegister


CLI_BUILTINS = AjcCommandRegister("BUILTINS")


@CLI_BUILTINS.register
def version(app):
    "Show the version of Ajiaco and exit"
    from .. import VERSION

    print(f"Ajiaco v.{VERSION}")


@CLI_BUILTINS.register(name="reset-storage")
def reset_storage(app, noinput: bool = False):
    "pass"
    if noinput:
        answer = "yes"
    else:
        answer = input("Do you want to cleat the database? [Yes/no] ").lower()

    while answer.lower() not in ("yes", "no"):
        answer = input("Please answer 'yes' or 'no': ").lower()

    if answer == "no":
        return

    storage = app.storage
    print(f"Target: {storage}")
    print("  - Deleting Storage...")
    if storage.exists():
        storage.drop_storage()

    print("  - Creating Storage...")
    storage.create_storage()

    print("  - Creating Schema...")
    storage.create_schema()

    print("  - Stamping...")
    storage.stamp()

    print("DONE!")


@CLI_BUILTINS.register()
def serve(app):
    """Run the uvicorn webserver"""
    return app.webapp.run(app)
