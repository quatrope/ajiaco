import code
import datetime as dt
import itertools as it

from IPython import start_ipython

import rich
from rich import progress, prompt, rule

from .register import AjcCommandRegister

from ..utils import sysinfo

from .cli_logo import CLI_LOGO


CLI_BUILTINS = AjcCommandRegister("BUILTINS")


@CLI_BUILTINS.register
def version(app):
    """Display Ajiaco version information.


    Display the current version of Ajiaco and exit. Useful for checking
    the installed version or including version information in bug reports.

    """
    rich.print(f"{CLI_LOGO} v.{app.version}")


@CLI_BUILTINS.register(name="reset-storage")
def reset_storage(app, noinput: bool = False):
    """Reset the database storage to its initial state.

    Completely resets the storage database by:

    1. Deleting the existing storage if it exists

    2. Creating a new storage

    3. Creating the schema

    4. Adding system information stamp

    This operation is irreversible. All existing data will be lost.
    Requires confirmation unless --noinput is specified.
    """
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


@CLI_BUILTINS.register(name="show-storage-stamp")
def show_storage_stamp(app):
    """Display storage metadata and creation information.

    Shows the stamp information stored in the database, including:

    - Creation timestamp

    - System information at creation time

    - Ajiaco version used to create the storage

    """
    with app.storage.transaction() as conn:
        stamp = conn.get_stamp()

    rich.print(stamp)


@CLI_BUILTINS.register()
def webserver(app, host: str = "localhost", port: int = 2501):
    """Start the Ajiaco web interface server.

    Launches a uvicorn web server that provides a web interface
    for interacting with Ajiaco. Using host 0.0.0.0 makes the server
    accessible from other machines. The server runs until interrupted
    with Ctrl+C.

    """
    now = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    rich.print(f"​{CLI_LOGO}​ v.{app.version}")
    rich.print(f"🦄 Starting Webserver - {now}")
    rich.print(rule.Rule())

    return app.webapp.run(app, host=host, port=port)


# =============================================================================
# SHELL
# =============================================================================


def _run_plain(slocals):
    """Run a plain Python interactive console.

    Parameters
    ----------
    slocals : dict
        Dictionary of local variables for the interactive session.

    Returns
    -------
    InteractiveConsole
        The console instance.
    """
    console = code.InteractiveConsole(slocals)
    console.interact("")
    return console


def _run_ipython(slocals):
    """Run an IPython interactive shell.

    Parameters
    ----------
    slocals : dict
        Dictionary of local variables for the interactive session.

    Returns
    -------
    IPythonShell
        The IPython shell instance.
    """
    return start_ipython(argv=[], user_ns=slocals)


def _create_banner(app, slocals):
    """Create a banner with application information for the shell.

    Parameters
    ----------
    app : AjiacoApp
        The main application instance.
    slocals : dict
        Dictionary of local variables to display in the banner.

    Returns
    -------
    str
        Formatted banner string.
    """
    lines = []
    bullets = it.cycle(("🔹", "🔸"))
    for lname, lvalue in sorted(slocals.items()):
        ltype = type(lvalue).__name__
        line = f"\t{next(bullets)} {lname}: {ltype!r}"
        lines.append(line)

    banner_parts = (
        [""]
        + [f"​{CLI_LOGO} v.{app.version}"]
        + [f"📦 Running inside: '{app.app_path}'"]
        + ["🏷️  Variables:"]
        + lines
        + [""]
    )

    banner = "\n".join(banner_parts)

    return banner


@CLI_BUILTINS.register()
def shell(app, plain: bool = False):
    """Launch an interactive Python shell with Ajiaco environment.

    Starts an interactive Python shell with the Ajiaco application context
    pre-loaded. By default uses IPython for enhanced features, but can
    fall back to plain Python shell if requested.

    The environment includes the following pre-loaded variables:

    - app: The main application instance

    - conn: Active database connection

    IPython shell provides enhanced features like tab completion.
    All database operations are executed within a transaction.
    Exit the shell with exit() or Ctrl+D.

    """
    slocals = {"app": app}

    with app.storage.transaction() as conn:
        slocals["conn"] = conn

        banner = _create_banner(app, slocals)
        rich.print(banner)
        rich.print(rule.Rule())

        shell = _run_plain if plain else _run_ipython
        return shell(slocals)
