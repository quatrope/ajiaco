import functools

import pydantic
from pydantic.dataclasses import dataclass, Field as field


class _Config:
    arbitrary_types_allowed = True


dataclass = functools.partial(dataclass, config=_Config)


validate_call = functools.partial(pydantic.validate_call, config=_Config)


def cfield(func=None, /, **kwargs):

    def dec(f: any):
        prop = property(f)
        return pydantic.computed_field(prop)

    if func is None:
        return dec

    return dec(func)
