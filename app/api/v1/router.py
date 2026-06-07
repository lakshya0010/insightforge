from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.repositories.user_repo import UserRepository
from app.models.user import User
import logging
from app.schemas.response import APIResponse
from app.services.parser_service import CSVParserService
from app.services.statement_service import StatementService
from app.schemas.statement import StatementOut, StatementDetailOut
from app.repositories.statement_repo import StatementRepository

router = APIRouter()
logger = logging.getLogger(__name__)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

def get_statement_service(db: AsyncSession = Depends(get_db))-> StatementService:
    repo = StatementRepository(db)
    parser = CSVParserService()
    return StatementService(repo, parser)


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
    
@router.get("/users/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse.ok(data = UserResponse.model_validate(current_user))


@router.post("/statements/upload", status_code=201)
async def upload_statement(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: StatementService = Depends(get_statement_service)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code= 400,
            detail="Only CSV file accepted"
        )
    
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    
    try:
        result = await service.upload_statement(user_id=current_user.id, file_content=content, filename=file.filename)
        return APIResponse.ok(data=result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/statements")
async def get_statements(
    current_user: User = Depends(get_current_user),
    service: StatementService=Depends(get_statement_service)
):
    results = await service.get_statements(current_user.id)
    return APIResponse.ok(data=results)


@router.get("/statements/{statement_id}")
async def get_statement(
    statement_id: int,
    current_user: User= Depends(get_current_user),
    service: StatementService = Depends(get_statement_service)
):
    try:
        result = await service.get_statement_detail(
            statement_id=statement_id,
            user_id=current_user.id
        )
        return APIResponse.ok(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

