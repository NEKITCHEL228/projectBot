from aiohttp.web import (Application as AiohttpApplication, Request as AiohttpRequest, View as AiohttpView)
from app.backend.web.config import setup_config
from app.backend.web.logger import setup_logging
from app.backend.web.middlewares import setup_middlewares
from app.backend.web.routes import setup_routes
from app.backend.web.config import Config
from app.backend.store.database import Database
from app.backend.store import setup_store, Store


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None

class Request(AiohttpRequest):
    pass

class View(AiohttpView):
    pass

app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    session_setup(app, EncryptedCookieStorage(app.config.session.key))
    setup_routes(app)
    setup_aiohttp_apispec(
        app, title="Telegram BirzjaGameBot", url="/docs/json", swagger_path="/docs"
    )
    setup_middlewares(app)
    setup_store(app)
    return app