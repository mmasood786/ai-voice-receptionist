from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, TenantMembership
from app.api.dependencies.auth import get_current_user


async def get_current_tenant_id(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> int:
    result = await db.execute(
        select(TenantMembership.tenant_id)
        .where(
            TenantMembership.user_id == current_user.id,
        )
        .order_by(TenantMembership.id)
        .limit(1)
    )

    tenant_id = result.scalar_one_or_none()

    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a tenant.",
        )

    return tenant_id