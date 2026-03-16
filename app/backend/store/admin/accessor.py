from typing import TYPE_CHECKING

from sqlalchemy import select

from app.backend.admin.models import AdminModel
from app.backend.base.base_accessor import BaseAccessor
from app.backend.web.utils import hash_password

if TYPE_CHECKING:
    from app.backend.web.app import Application

class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        admin_tg_id = self.app.config.admin.tg_id
        admin_password = self.app.config.admin.password
        
        admin = await self.get_by_tg_id(admin_tg_id)
        if not admin:
            await app.store.admins.create_admin(admin_tg_id, admin_password)

    async def get_by_tg_id(self, tg_id: str):
        query = select(AdminModel).where(AdminModel.tg_id == tg_id)
        
        async with self.app.database.session() as session:
            result = await session.execute(query)
            admin = result.scalar_one_or_none()
            return admin

    async def create_admin(self, tg_id: str, password: str):
        admin = AdminModel(tg_id=tg_id, password_hash=hash_password(password))
        
        async with self.app.database.session() as session:
            session.add(admin)
            await session.commit()
            
        return admin
    
    async def get_list_admins(self):
        query = select(AdminModel)
        
        async with self.app.database.session() as session:
            result = await session.execute(query)
            admins = result.scalars().all()
            return admins