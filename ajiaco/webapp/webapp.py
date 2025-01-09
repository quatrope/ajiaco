import attrs

from starlette.applications import Starlette

import uvicorn

from . import routes

@attrs.define(frozen=True)
class AjcWebApp:

    webapp: Starlette = attrs.field(init=False, repr=False)
    uvicorn_kwargs: dict = attrs.field(converter=dict)

    @webapp.default
    def _webapp_default(self):
        the_webapp = Starlette(routes=routes.ROUTES)
        return the_webapp

    @uvicorn_kwargs.default
    def _uvicorn_kwargs_default(self):
        return {}

    # API =============================================================================

    def run(self, app):
        the_webapp = self.webapp
        the_kwargs = self.uvicorn_kwargs
        return uvicorn.run(the_webapp, **the_kwargs)
