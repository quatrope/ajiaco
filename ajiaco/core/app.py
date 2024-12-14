import pathlib

import attrs
from attrs import validators as valids

from ..storage import Storage

# =============================================================================
# MAIN PROJECT CLASS
# =============================================================================


def _coerce_storage(value):
    if isinstance(value, str):
        value = Storage.from_url(value)
    return value


@attrs.define(frozen=True)
class Application:
    """Represent a whole Ajiaco project.

    This object containt the instances of the games and also has api capable
    of call the command line interface.

    """

    filename: str = attrs.field(validator=valids.instance_of(str))
    secret: str = attrs.field(validator=valids.instance_of(str), repr=False)
    verbose: int = attrs.field(
        converter=int,
        validator=valids.and_(
            valids.instance_of(int), valids.ge(0), valids.le(3)
        ),
    )
    storage: Storage = attrs.field(
        converter=(lambda v: Storage.from_url(v) if isinstance(v, str) else v),
        validator=valids.instance_of(Storage),
        repr=False,
    )

    _experiment_sessions_defaults: dict = attrs.field(
        init=False,
        factory=dict,
        validator=valids.instance_of(dict),
        repr=False,
    )

    # DEFAULTS ================================================================

    @storage.default
    def _storage_default(self):
        path = self.app_path / "database.sqlite3"
        return Storage.from_url(f"sqlite:///{path}")

    # API =====================================================================

    @property
    def app_path(self):
        path = pathlib.Path(self.filename)
        return path.absolute().parent

    @property
    def experiment_sessions_default(self):
        return dict(self._experiment_sessions_defaults)

    def set_experiment_sessions_defaults(self, **kwargs):
        if "name" in kwargs:
            raise ValueError("'name' can't be default")
        self._experiment_sessions_defaults.update(kwargs)

    # SCHEMA = {

    #     "auth_level": vol.In(AUTH_LEVELS),
    #     "admin_username": str,
    #     "admin_password": str,
    #     "currency": vol.In(CURRENCIES),
    #     "language": vol.In(LANGUAGES),
    #     "database": db.Database,
    #     "session_defaults": dict,
    #     "commands": cli.CommandRegister,
    #     "experiments": OrderedDict}

    # FROZEN_SCHEMA = True

    # def __repr__(self):
    #     return f"Project(prjpath='{self.prjpath()}', debug={self.debug})"

    # def __init__(self, filename, secret, debug=True, dbpath=None,
    #              auth_level=None, admin_username=None,
    #              admin_password=None, currency=None, language=None):
    #     self.filename = filename
    #     self.secret = secret
    #     self.debug = debug or env.env("AJIACO_DEBUG", c=bool, d=False)

    #     self.auth_level = (
    #         auth_level or env.env("AJIACO_AUTH_LEVEL", d=AUTH_LEVEL_DEMO))
    #     self.admin_username = (
    #         admin_username or env.env("AJIACO_ADMIN_USERNAME", d="admin"))
    #     self.admin_password = passenc.hash(
    #         admin_password or env.env("AJIACO_ADMIN_PASSWORD", d="admin"))

    #     self.currency = (
    #         currency or env.env("AJIACO_CURRENCY", d=CURRENCY_POINTS))
    #     self.language = language or env.env("AJIACO_LANGUAGE", d=LANG_EN)

    #     if dbpath is None:
    #         default = os.path.join(self.prjpath(), "database.sqlite3")
    #         dbpath = env.env("AJIACO_DBPATH", d=f"sqlite:///{default}")

    #     self.database = db.Database(dbpath, self)

    #     self.session_defaults = {}

    #     self.commands = cli.CommandRegister("Customs")
    #     self.experiments = OrderedDict()
