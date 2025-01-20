import inspect
import logging
import pathlib

import attrs
from attrs import validators as valids

from .cli import AjcCommandRegister, AjcCLIManager, CLI_BUILTINS
from .storage import AjcStorage
from .webapp import AjcWebApp


VERBOSE_TO_LOGGING = {
    0: logging.CRITICAL,  # 50
    1: logging.ERROR,  # 40
    2: logging.WARNING,  # 30
    3: logging.INFO,  # 20
    4: logging.DEBUG,  # 10
}

# =============================================================================
# MAIN PROJECT CLASS
# =============================================================================


@attrs.define(frozen=True)
class AjcApplication:
    """Represent a whole Ajiaco project.

    This object containt the instances of the games and also has api capable
    of call the command line interface.

    """

    _created_at_frame: object = attrs.field(init=False, repr=False)

    filename: str = attrs.field(validator=valids.instance_of(str))
    secret: str = attrs.field(validator=valids.instance_of(str), repr=False)
    verbose: int = attrs.field(
        converter=int,
        validator=valids.and_(
            valids.instance_of(int), valids.ge(0), valids.le(3)
        ),
    )
    debug: bool = attrs.field(converter=bool)

    logger: logging.Logger = attrs.field(init=False, repr=False)

    storage: AjcStorage = attrs.field(
        converter=(
            lambda v: AjcStorage.from_url(v) if isinstance(v, str) else v
        ),
        validator=valids.instance_of(AjcStorage),
        repr=False,
    )

    commands: AjcCommandRegister = attrs.field(init=False, repr=False)

    webapp: AjcWebApp = attrs.field(init=False, repr=False)

    _experiment_sessions_defaults: dict = attrs.field(init=False, repr=False)

    # DEFAULTS ================================================================

    @_created_at_frame.default
    def _created_at_frame_default(self):
        # two f_back for the attrs.__init__
        return inspect.currentframe().f_back.f_back

    @storage.default
    def _storage_default(self):
        path = self.filepath.parent / "database.sqlite3"

        log_level = VERBOSE_TO_LOGGING.get(self.verbose, logging.CRITICAL)
        echo = log_level <= logging.INFO

        return AjcStorage.from_url(f"sqlite:///{path}", echo=echo)

    @commands.default
    def _commands_default(self):
        name = f"Commands of '{self.filepath}'"
        return AjcCommandRegister(name=name, not_available=CLI_BUILTINS)

    @logger.default
    def _logger_default(self):
        logger = logging.getLogger(self.filename)

        log_level = VERBOSE_TO_LOGGING.get(self.verbose, logging.CRITICAL)
        logger.setLevel(log_level)

        return logger

    @webapp.default
    def _webapp_default(self):
        return AjcWebApp(app=self)

    @_experiment_sessions_defaults.default
    def _experiment_sessions_default(self):
        return {}

    # API =====================================================================

    @property
    def filepath(self):
        return pathlib.Path(self.filename)

    @property
    def icfn(self):
        for k, v in self._created_at_frame.f_locals.items():
            if v is self:
                return k
        raise ValueError("Unable to find instance creation name")

    @property
    def version(self):
        from . import VERSION

        return VERSION

    @property
    def experiment_sessions_default(self):
        return dict(self._experiment_sessions_defaults)

    def set_experiment_sessions_defaults(self, **kwargs):
        if "name" in kwargs:
            raise ValueError("'name' can't be default")
        self._experiment_sessions_defaults.update(kwargs)

    def run_from_command_line(self):
        cli_manager = AjcCLIManager(commands=[self.commands, CLI_BUILTINS])
        return cli_manager.parse_and_run(app=self)
