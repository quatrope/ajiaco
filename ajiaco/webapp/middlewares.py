from starlette.middleware.base import BaseHTTPMiddleware


class AjcMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ajc_app, templates):
        super().__init__(app)
        self.ajc_app = ajc_app
        self.templates = templates

    async def dispatch(self, request, call_next):
        request.state.app = self.ajc_app
        request.state.templates = self.templates
        response = await call_next(request)
        return response
