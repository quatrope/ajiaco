
# =============================================================================
# MAIN PROJECT CLASS
# =============================================================================

@dataclass(frozen=True)
class Application:
    """Represent a whole Ajiaco project.

    This object containt the instances of the games and also has api capable
    of call the command line interface.

    """
    filename

    SCHEMA = {
        "filename": str,
        "secret": str,
        "debug": bool,
        "auth_level": vol.In(AUTH_LEVELS),
        "admin_username": str,
        "admin_password": str,
        "currency": vol.In(CURRENCIES),
        "language": vol.In(LANGUAGES),
        "database": db.Database,
        "session_defaults": dict,
        "commands": cli.CommandRegister,
        "experiments": OrderedDict}

    FROZEN_SCHEMA = True

    def __repr__(self):
        return f"Project(prjpath='{self.prjpath()}', debug={self.debug})"

    def __init__(self, filename, secret, debug=True, dbpath=None,
                 auth_level=None, admin_username=None,
                 admin_password=None, currency=None, language=None):
        self.filename = filename
        self.secret = secret
        self.debug = debug or env.env("AJIACO_DEBUG", c=bool, d=False)

        self.auth_level = (
            auth_level or env.env("AJIACO_AUTH_LEVEL", d=AUTH_LEVEL_DEMO))
        self.admin_username = (
            admin_username or env.env("AJIACO_ADMIN_USERNAME", d="admin"))
        self.admin_password = passenc.hash(
            admin_password or env.env("AJIACO_ADMIN_PASSWORD", d="admin"))

        self.currency = (
            currency or env.env("AJIACO_CURRENCY", d=CURRENCY_POINTS))
        self.language = language or env.env("AJIACO_LANGUAGE", d=LANG_EN)

        if dbpath is None:
            default = os.path.join(self.prjpath(), "database.sqlite3")
            dbpath = env.env("AJIACO_DBPATH", d=f"sqlite:///{default}")

        self.database = db.Database(dbpath, self)

        self.session_defaults = {}

        self.commands = cli.CommandRegister("Customs")
        self.experiments = OrderedDict()
