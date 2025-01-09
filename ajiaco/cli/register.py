import functools
import inspect
from collections import abc, OrderedDict

import attrs

from ..utils import rtc


@attrs.define(frozen=True)
class AjcCommandTemplate:
    name: str
    function: str
    signature: inspect.Signature

    def bind(self, ajc_app):
        function = self.function
        signature = self.signature

        params_without_app = [
            param
            for pname, param in signature.parameters.items()
            if pname != "app"
        ]

        @functools.wraps(function)
        def command_function(*args, **kwargs):
            return function(app=ajc_app, *args, **kwargs)

        command_function.__signature__ = signature.replace(
            parameters=params_without_app
        )

        return command_function


@attrs.define(frozen=True)
class AjcCommandRegister(abc.Mapping):

    name: str = attrs.field(converter=str)
    not_available: frozenset[str] = attrs.field(
        converter=frozenset,
        factory=frozenset,
        repr=False,
    )
    commands_templates: OrderedDict[str, AjcCommandTemplate] = attrs.field(
        init=False, factory=OrderedDict, repr=False
    )

    def __getitem__(self, k):
        return self.commands_templates[k]

    def __iter__(self):
        return iter(self.commands_templates)

    def __len__(self):
        return len(self.commands_templates)

    @rtc.validate_call
    def register(
        self, func: abc.Callable | None = None, name: str | None = None
    ):
        provided_name = name

        @rtc.validate_call
        def _dec(function: abc.Callable):
            name = (
                function.__name__ if provided_name is None else provided_name
            )
            if name in self.not_available:
                raise ValueError(f"command with name {name!r}  is not alowed")

            signature = inspect.signature(function)
            app_parameter = signature.parameters.get("app")
            if app_parameter is None:
                raise ValueError(
                    f"Missing parameter 'app' in Command {name!r}"
                )
            elif app_parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
                raise ValueError(
                    f"Parameter 'app' in Command {name!r} "
                    "need to be used as keyword argument"
                )

            self.commands_templates[name] = AjcCommandTemplate(
                name=name, function=function, signature=signature
            )
            return function

        if func is None:
            return _dec
        return _dec(func)
