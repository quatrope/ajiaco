from starlette import responses
from starlette import endpoints
from starlette.routing import Route


class AjcEndpoint:
    @classmethod
    def get_path(cls):
        return cls.path

    @classmethod
    def as_route(cls):
        return Route(cls.get_path(), endpoint=cls)


class HomePage(AjcEndpoint, endpoints.HTTPEndpoint):
    path = "/"

    async def get(self, request):
        return responses.PlainTextResponse(f"Hello, world!")


# =============================================================================
# THE ROUTES
# =============================================================================

ROUTES = [
    HomePage.as_route(),
]
