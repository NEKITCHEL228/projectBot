from aiohttp.web import (Application as AiohttpApplication, Request as AiohttpRequest, View as AiohttpView)

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