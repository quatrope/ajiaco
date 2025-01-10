import attrs

from starlette.applications import Starlette

import uvicorn

from . import routes


@attrs.define(frozen=True)
class AjcWebApp:

    webapp: Starlette = attrs.field(init=False, repr=False)

    @webapp.default
    def _webapp_default(self):
        the_webapp = Starlette(routes=routes.ROUTES)
        return the_webapp

    # API =============================================================================

    def run(self, app, **uvicorn_kwargs):
        the_webapp = self.webapp
        return uvicorn.run(the_webapp, **uvicorn_kwargs)
