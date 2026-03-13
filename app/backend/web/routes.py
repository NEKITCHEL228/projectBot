from app.backend.admin.routes import setup_admin_routes
from app.backend.game.routes import setup_game_routes
from app.backend.web.app import Application

def setup_routes(app: Application):
    setup_admin_routes(app)
    setup_game_routes(app)