from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.repositories.user_repo import UserRepository
from app.models.user import User
import logging
from app.schemas.response import APIResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

@router.get("/health")
async def health_check():
    return APIResponse.ok(data={"status":"ok"})

@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    try:
        result = await service.create_user(user)
        logger.info(f"New user registered: {result.email}")
        return APIResponse.ok(data=result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/auth/login", response_model=APIResponse[TokenResponse])
async def login(
    credentials: LoginRequest,
    service: UserService = Depends(get_user_service)
):
    try:
        result = await service.login(credentials.email, credentials.password)
        logger.info(f"User logged in: {credentials.email}")
        return APIResponse.ok(data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse.ok(data = UserResponse.model_validate(current_user))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id:int, service: UserService = Depends(get_user_service), _:User = Depends(get_current_user)):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return APIResponse.ok(data=user)

