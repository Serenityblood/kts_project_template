from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.abc import Request

if TYPE_CHECKING:
    from .app import Application


@web.middleware
async def example_mw(request: Request, handler):

    return await handler(request)


def setup_middleware(app: "Application"):
    app.middlewares.append(example_mw)
