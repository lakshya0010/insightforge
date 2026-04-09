from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: UserCreate, hashed_password:str)-> User:
        user = User(name=user_data.name, email=user_data.email, hashed_password = hashed_password)

        self.db.add(user)
        await self.db.commit()

        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    

    async def get_by_email(self, email:str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    

