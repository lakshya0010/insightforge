from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()
user_service = UserService()

def get_user_service():
    return user_service

@router.get("/health")
async def health_check():
    return{"status":"ok"}

@router.post("/users", response_model=UserResponse)
async def create_user(user:UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(user)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id:int, service: UserService = Depends(get_user_service)):
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return user

