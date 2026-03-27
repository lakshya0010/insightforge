from app.schemas.user import UserCreate, UserResponse
from typing import List, Optional

class UserService:
    def __init__(self):
        self._users: List[UserResponse] = []
        self._id_counter = 1
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        user = UserResponse(
            id=self._id_counter,
            name=user_data.name,
            email=user_data.email
        )
        self._users.append(user)
        self._id_counter += 1
        return user
    
    def get_user(self, user_id:int) -> Optional[UserResponse]:
        for user in self._users:
            if user.id == user_id:
                return user
        return None
    
