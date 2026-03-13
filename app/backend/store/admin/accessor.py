from typing import TYPE_CHECKING

from app.backend.base.base_accessor import BaseAccessor

if TYPE_CHECKING:
    from app.backend.web.app import Application

class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        pass

    async def get_by_tg_id(self, tg_id: str):
        
        
        return None

    async def create_admin(self, tg_id: str):
        pass