import collections
import code
import pprint

from IPython import start_ipython

from .register import AjcCommandRegister

from ..utils import sysinfo


CLI_BUILTINS = AjcCommandRegister("BUILTINS")


@CLI_BUILTINS.register
def version(app):
    "Show the version of Ajiaco and exit"
    print(f"Ajiaco v.{app.version}")


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
    stamp_data = sysinfo.info_dict()
    stamp_data["AJIACO_VERSION"] = app.version
    with storage.transaction() as conn:
        conn.stamp(stamp_data)

    print("DONE!")


@CLI_BUILTINS.register(name="storage-stamp")
def storage_stamp(app):
    """Show the stamp inside the storage"""
    with app.storage.transaction() as conn:
        stamp = conn.get_stamp()
    pprint.pprint(stamp)


@CLI_BUILTINS.register()
def serve(app):
    """Run the uvicorn webserver"""
    return app.webapp.run(app)


# =============================================================================
# SHELL
# =============================================================================


def _run_plain(slocals, banner):
    console = code.InteractiveConsole(slocals)
    console.interact(banner)


def _run_ipython(slocals, banner):
    start_ipython(
        argv=["--TerminalInteractiveShell.banner2={}".format(banner)],
        user_ns=slocals,
    )


def _create_banner(app, slocals):

    by_module = collections.defaultdict(list)
    for k, v in slocals.items():
        module_name = getattr(v, "__module__", None) or ""
        by_module[module_name].append(k)

    lines = []
    for module_name, imported in sorted(by_module.items()):
        prefix = ", ".join(imported)
        suffix = "({})".format(module_name) if module_name else ""
        line = "\t>>> {} {}".format(prefix, suffix)
        lines.append(line)

    banner_parts = (
        [f"Ajiaco Version: \n\t{app.version}"]
        + [f"Running inside: \n\t{app.app_path}"]
        + ["Ajiaco Variables:"]
        + lines
        + [""]
    )

    banner = "\n".join(banner_parts)

    return banner


@CLI_BUILTINS.register()
def shell(app, plain: bool = False):
    """Run the Python shell inside Ajiaco environment"""
    slocals = {"app": app}

    with app.storage.transaction() as conn:
        slocals["conn"] = conn
        banner = _create_banner(app, slocals)
        shell = _run_plain if plain else _run_ipython
        return shell(slocals, banner)
