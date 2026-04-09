from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.repositories.user_repo import UserRepository
from app.models.user import User


router = APIRouter()

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

@router.get("/health")
async def health_check():
    return{"status":"ok"}

@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    try:
        return await service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    service: UserService = Depends(get_user_service)
):
    try:
        return await service.login(credentials.email, credentials.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user:UserCreate, service: UserService = Depends(get_user_service)):
    try:
        return await service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id:int, service: UserService = Depends(get_user_service), _:User = Depends(get_current_user)):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return user

