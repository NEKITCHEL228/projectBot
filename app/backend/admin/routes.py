import typing

if typing.TYPE_CHECKING:
    from app.backend.web.app import Application


def setup_admin_routes(_app: "Application") -> None:
    pass
