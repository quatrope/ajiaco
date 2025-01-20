import os
import pathlib

import attrs

from jinja2 import Environment, FileSystemLoader

from starlette.templating import Jinja2Templates
from starlette.applications import Starlette
from starlette.middleware import Middleware

import uvicorn

from . import routes
from .middlewares import AjcMiddleware


# =============================================================================
# CONSTANTS
# =============================================================================

PATH = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

TEMPLATE_PATH = PATH / "templates"

STATIC_PATH = PATH / "static"

# =============================================================================
# THE CLASS
# =============================================================================


@attrs.define(frozen=True)
class AjcWebApp:

    app: object = attrs.field()
    templates: Jinja2Templates = attrs.field(init=False)
    middleware: list[Middleware] = attrs.field(init=False, repr=False)
    webapp: Starlette = attrs.field(init=False, repr=False)

    @templates.default
    def _templates_default(self):
        env = Environment(loader=FileSystemLoader(self.template_dirs))
        return Jinja2Templates(env=env)

    @middleware.default
    def _middleware_default(self):
        app, templates = self.app, self.templates
        return (Middleware(AjcMiddleware, ajc_app=app, templates=templates),)

    @webapp.default
    def _webapp_default(self):
        the_webapp = Starlette(
            routes=[
                routes.About.as_route(),
                routes.MultiDirectoryStaticFiles.as_route(self.static_dirs),
            ],
            debug=self.app.debug,
            middleware=self.middleware,
        )
        return the_webapp

    # API =====================================================================

    @property
    def static_dirs(self):
        return (
            self.app.filepath.parent / "static",
            STATIC_PATH,
        )

    @property
    def template_dirs(self):
        return (
            self.app.filepath.parent / "templates",
            TEMPLATE_PATH,
        )

    def run(self, app, **uvicorn_kwargs):
        the_webapp = f"{app.filepath.stem}:{app.icfn}.webapp.webapp"
        return uvicorn.run(the_webapp, **uvicorn_kwargs)
