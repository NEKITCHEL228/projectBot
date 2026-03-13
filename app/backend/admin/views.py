from app.backend.web.utils import check_admin_auth
from aiohttp.web_exceptions import HTTPBadRequest, HTTPUnauthorized, HTTPForbidden
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session, get_session
from app.backend.store.admin.accessor import AdminAccessor

from app.backend.admin.schemes import AdminSchema
from app.backend.web.app import View

class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = await self.request.json()
        if not data:
            raise HTTPUnauthorized(reason="Missing JSON body")
        admin = await self.app.store.get_admin_by_tg_id(data["tg_id"])
        if not admin or not check_admin_auth(":".join([data["tg_id"], data["password_hash"]]), self.app.config.admin.tg_id, self.app.config.admin.password):
            raise HTTPForbidden(reason="Invalid credentials")
        
        session = await new_session(self.request)
        session["admin"] = {"tg_id": admin.tg_id, "id": admin.id}
        return {"tg_id": admin.tg_id, "id": admin.id}