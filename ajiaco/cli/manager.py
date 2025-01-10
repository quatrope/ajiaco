import attrs
from attrs import validators as valids

import typer

from .register import AjcCommandRegister
from .cli_logo import CLI_LOGO


_TYPER_CONFIG = {
    "help": "{CLI_LOGO} command-line interface",
    "no_args_is_help": True,
}


@attrs.define(frozen=True)
class AjcCLIManager:

    commands: [AjcCommandRegister] = attrs.field(
        converter=tuple,
        validator=valids.deep_iterable(
            member_validator=valids.instance_of(AjcCommandRegister),
            iterable_validator=valids.instance_of(tuple),
        ),
    )

    def make_cli_app(self, app):
        typer_app = typer.Typer(**_TYPER_CONFIG)
        for register in self.commands:
            for name, cmd_template in register.items():
                command_function = cmd_template.bind(app)
                decorator = typer_app.command(name=name)
                decorator(command_function)
        return typer_app

    def parse_and_run(self, app):
        cli_app = self.make_cli_app(app)
        return cli_app()
