from aiohttp.web import Application

def setup_routes(app: Application):
    from app.backend.admin.routes import setup_admin_routes
    from app.backend.game.routes import setup_game_routes
    
    setup_admin_routes(app)
    setup_game_routes(app)