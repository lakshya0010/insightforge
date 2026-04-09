from app.schemas.user import UserCreate, UserResponse, TokenResponse
from typing import List, Optional
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token

class UserService:
    def __init__(self, repo:UserRepository):
        self.repo = repo
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        existing = await self.repo.get_by_email(user_data.email)
        if existing:
            raise ValueError(f"Email {user_data.email} already exists.")
        hashed = hash_password(user_data.password)
        user = await self.repo.create(user_data, hashed)
        return UserResponse.model_validate(user)
    

    async def login(self, email: str, password:str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=token)
    
    async def get_user(self, user_id:int) -> Optional[UserResponse]:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)
    
