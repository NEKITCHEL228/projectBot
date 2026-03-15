import typing

if typing.TYPE_CHECKING:
    from app.backend.web.app import Application


def setup_admin_routes(app: "Application") -> None:
    from app.backend.admin.views import AdminLoginView, AdminCurrentView
    
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
