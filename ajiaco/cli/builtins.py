import code
import datetime as dt
import itertools as it

from IPython import start_ipython

import rich
from rich import progress, prompt, rule

from .register import AjcCommandRegister

from ..utils import sysinfo


AJC = "🥔🌽🍗🌿"

CLI_BUILTINS = AjcCommandRegister("BUILTINS")


@CLI_BUILTINS.register
def version(app):
    "Show the version of Ajiaco and exit"

    rich.print(f"​{AJC}​ Ajiaco v.{app.version}")


@CLI_BUILTINS.register(name="reset-storage")
def reset_storage(app, noinput: bool = False):
    "pass"

    answer = noinput or prompt.Confirm.ask(
        "⚠️  Do you want to clear the database?"
    )

    if not answer:
        return

    storage = app.storage

    rich.print(f"​🎯​ Target -- {storage}")

    with rich.progress.Progress(
        progress.SpinnerColumn(),
        progress.TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as prgss:
        if storage.exists():
            prgss.add_task(description="- Deleting Old Storage", total=None)
            storage.drop_storage()

        prgss.add_task(description="- Creating Storage​")
        storage.create_storage()

        prgss.add_task(description="- Creating Schema")
        storage.create_schema()

        prgss.add_task(description="- Stamping")
        stamp_data = sysinfo.info_dict()
        stamp_data["AJIACO_VERSION"] = app.version
        with storage.transaction() as conn:
            conn.stamp(stamp_data)

    rich.print("🏁 DONE")


@CLI_BUILTINS.register(name="storage-stamp")
def storage_stamp(app):
    """Show the stamp inside the storage"""
    with app.storage.transaction() as conn:
        stamp = conn.get_stamp()

    rich.print(stamp)


@CLI_BUILTINS.register()
def webserver(app, host: str = "localhost", port: int = 2501):
    """Run the uvicorn webserver"""

    rich.print(f"​{AJC}​ Starting Webserver for Ajiaco v.{app.version}")
    rich.print(f"⏰ {dt.datetime.now()}")

    return app.webapp.run(app, host=host, port=port)


# =============================================================================
# SHELL
# =============================================================================


def _run_plain(slocals):
    console = code.InteractiveConsole(slocals)
    console.interact("")
    return console


def _run_ipython(slocals):
    return start_ipython(argv=[], user_ns=slocals)


def _create_banner(app, slocals):

    lines = []
    bullets = it.cycle(("🔹", "🔸"))
    for lname, lvalue in sorted(slocals.items()):
        ltype = type(lvalue).__name__
        line = f"\t{next(bullets)} {lname}: {ltype!r}"
        lines.append(line)

    banner_parts = (
        [""]
        + [f"​{AJC}​ Ajiaco v.{app.version}"]
        + [f"📦 Running inside: '{app.app_path}'"]
        + ["🏷️  Variables:"]
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
        rich.print(banner)
        rich.print(rule.Rule())

        shell = _run_plain if plain else _run_ipython
        return shell(slocals)
