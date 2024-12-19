import functools

import pydantic


class _Config:
    arbitrary_types_allowed = True


validate_call = functools.partial(pydantic.validate_call, config=_Config)
