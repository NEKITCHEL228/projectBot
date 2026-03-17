from aiohttp.web import (Application as AiohttpApplication, Request as AiohttpRequest, View as AiohttpView)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64

from app.backend.web.config import setup_config, Config
from app.backend.web.logger import setup_logging
from app.backend.web.middlewares import setup_middlewares
from app.backend.web.routes import setup_routes
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
    setup_logging()
    setup_config(app, config_path)
    setup_routes(app)
    setup_aiohttp_apispec(
        app, title="Telegram BirzjaGameBot", url="/docs/json", swagger_path="/docs"
    )
    session_setup(app, EncryptedCookieStorage(base64.urlsafe_b64decode(app.config.session.key)))
    setup_middlewares(app)
    setup_store(app)
    
    return app