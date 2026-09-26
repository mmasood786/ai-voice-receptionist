from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.tenant import get_current_tenant_id

from app.db.models import User

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    tenant_id: int


@router.post("/register")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long.",
        )

    service = AuthService(db)

    try:
        user = await service.create_user(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
            tenant_id=payload.tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
    
@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)

    result = await service.login(
        email=str(payload.email),
        password=payload.password,
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    user, access_token = result

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )
    
@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }
    
@router.get("/tenant")
async def get_my_tenant(
    tenant_id: int = Depends(get_current_tenant_id),
):
    return {
        "tenant_id": tenant_id,
    }
    
@router.get("/overview")
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_overview(
        tenant_id=tenant_id,
    )