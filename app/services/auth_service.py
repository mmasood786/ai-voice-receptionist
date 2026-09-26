from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, TenantMembership, Tenant
from app.services.password_service import hash_password

from app.services.password_service import verify_password
from app.services.token_service import create_access_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None,
        tenant_id: int,
        role: str = "owner",
    ) -> User:
        email = email.strip().lower()

        # Check whether the user already exists.
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("A user with this email already exists.")


        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise ValueError("Tenant not found.")

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
        )

        self.db.add(user)

        # Flush so user.id is available before creating membership.
        await self.db.flush()

        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant_id,
            role=role,
        )

        self.db.add(membership)

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        await self.db.refresh(user)

        return user
    
    
    async def login(
        self,
        *,
        email: str,
        password: str,
    ) -> tuple[User, str] | None:
        email = email.strip().lower()

        result = await self.db.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        access_token = create_access_token(
            user_id=user.id,
        )

        return user, access_token