import inspect
import functools

import attrs
from attrs import validators as valids

import typer

from .register import CommandRegister


_TYPER_CONFIG = {
    "help": "foo",
    "no_args_is_help": True,
}


@attrs.define(frozen=True)
class CLIManager:

    app: object
    commands: [CommandRegister] = attrs.field(
        converter=tuple,
        validator=valids.deep_iterable(
            member_validator=valids.instance_of(CommandRegister),
            iterable_validator=valids.instance_of(tuple),
        ),
    )

    def make_cli_app(self):
        typer_app = typer.Typer(**_TYPER_CONFIG)
        for register in self.commands:
            for name, cmd_template in register.items():
                command_function = cmd_template.bind(self.app)
                decorator = typer_app.command(name=name)
                decorator(command_function)
        return typer_app

    def parse_and_run(self):
        cli_app = self.make_cli_app()
        return cli_app()
