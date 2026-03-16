from sqlalchemy import select

from app.backend.user.models import UserModel
from app.backend.base.base_accessor import BaseAccessor

class UserAccessor(BaseAccessor):
    async def get_by_tg_id(self, tg_id: str):
        query = select(UserModel).where(UserModel.tg_id == tg_id)
        
        async with self.app.database.session() as session:
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user

    async def create_user(self, tg_id: str, name: str = ""):
        user = UserModel(tg_id=tg_id, name=name)
        
        async with self.app.database.session() as session:
            session.add(user)
            await session.commit()
            
        return user
    
    async def get_list_users(self):
        query = select(UserModel)
        
        async with self.app.database.session() as session:
            result = await session.execute(query)
            users = result.scalars().all()
            return users