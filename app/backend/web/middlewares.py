import json
import typing

from aiohttp.web import middleware, Response
from aiohttp.web_exceptions import HTTPException
if typing.TYPE_CHECKING:
    from app.backend.web.app import Application


@middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except HTTPException as e:
        return Response(
            status=e.status,
            body=json.dumps({"status": "error", "message": str(e)}),
            content_type="application/json",
        )
    except Exception:
        return Response(
            status=500,
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            content_type="application/json",
        )


def setup_middlewares(app: "Application") -> None:
    app.middlewares.append(error_middleware)
