import os
import pathlib

from starlette import endpoints
from starlette.routing import Route
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from .. import res

# =============================================================================
# CONF OF JINJA 2
# =============================================================================

PATH = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

TEMPLATE_PATH = PATH / "templates"

STATIC_PATH = PATH / "static"

AVAILABLE_METHODS = ("GET", "POST")


# =============================================================================
# ABSTRACT
# =============================================================================


class AjcEndpointMixin:
    abstract = True
    required_attrs = ["name", "path"]

    def __init_subclass__(cls):
        if vars(cls).get("abstract"):
            return
        required_attrs = list(getattr(cls, "required_attrs", []))
        for scls in cls.mro():
            if issubclass(scls, AjcEndpointMixin):
                required_attrs.extend(scls.required_attrs)
        for required in reversed(required_attrs):
            getattr(cls, required)

    @classmethod
    def as_route(cls):
        return Route(
            cls.path, endpoint=cls, methods=cls.methods, name=cls.name
        )


class MultiDirectoryStaticFiles(AjcEndpointMixin, StaticFiles):
    name = "static"
    path = "/static"

    def __init__(self, directories, **kwargs) -> None:
        super().__init__(**kwargs)
        self.all_directories.extend(directories)

    @classmethod
    def as_route(cls, directories):
        return Mount(
            cls.path,
            app=cls(directories=directories),
            name=cls.name,
        )


class TemplateEndpointMixin(AjcEndpointMixin):
    required_attrs = ["template", "methods"]
    abstract = True

    def __init_subclass__(cls):
        methods_diff = set(cls.methods).difference(AVAILABLE_METHODS)
        if methods_diff:
            raise ValueError(f"Unknow(s) method(s) {methods_diff}")

    @classmethod
    def get_template(cls):
        return cls.template

    def render(self, request, **context):
        """This is for making some extra context variables available to
        the template

        """
        templates = request.state.templates

        context.update(
            {
                "app": request.state.app,
                "request": request,
                "AJC_EMOJI": res.AJC_EMOJI,
            }
        )
        response = templates.TemplateResponse(
            request, self.template, context=context
        )
        return response


# =============================================================================
# ADMIN
# =============================================================================


class About(TemplateEndpointMixin, endpoints.HTTPEndpoint):
    name = "about"
    path = "/"
    template = "admin/About.html"  # TODO: cambiar por un path
    methods = ["GET"]

    async def get(self, request):
        return self.render(request)
