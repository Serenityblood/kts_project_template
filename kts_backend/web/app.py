import os
from typing import Sequence, Callable, Optional

from aiohttp.web import Application as AiohttpApplication


from kts_backend.store import setup_store, Store
from kts_backend.store.database import Database
from .config import setup_config, Config
from .mw import setup_middleware


class Application(AiohttpApplication):
    config = None
    store: Store or None = None
    database: Database or None = None


app = Application()


def setup_app(config_path: str) -> Application:
    setup_config(app, config_path)
    setup_middleware(app)
    setup_store(app)
    return app


application = setup_app(os.path.join(os.path.dirname(__file__), "..", "..", "etc/config.yaml"))