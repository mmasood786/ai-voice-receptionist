from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.dashboard import (
    DashboardConversationsResponse,
    DashboardKnowledgeResponse,
    DashboardLeadsResponse,
    DashboardOverviewResponse,
    DashboardRecentActivityResponse,
    DashboardAppointmentsResponse,
)
from app.services.dashboard_service import DashboardService
from app.api.dependencies.tenant import get_current_tenant_id

import logging


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


logger = logging.getLogger(__name__)

@router.get("/overview", response_model=DashboardOverviewResponse)
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_overview(
        tenant_id=tenant_id,
    )

@router.get(
    "/recent-activity",
    response_model=DashboardRecentActivityResponse,
)
# async def dashboard_recent_activity(
#     db: AsyncSession = Depends(get_db),
#     tenant_id: int = Depends(get_current_tenant_id),
# ):
#     service = DashboardService(db)

#     return await service.get_recent_activity(
#         tenant_id=tenant_id,
#     )



async def dashboard_recent_activity(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    try:
        service = DashboardService(db)

        items = await service.get_recent_activity(
            tenant_id=tenant_id,
        )

        return DashboardRecentActivityResponse(
            items=items,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch recent activity for tenant_id=%s",
            tenant_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve recent activity.",
        )

 
@router.get("/conversations")
async def conversations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_conversations(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/leads",
    response_model=DashboardLeadsResponse,
)
async def dashboard_leads(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_leads(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/appointments",
    response_model=DashboardAppointmentsResponse,
)
async def dashboard_appointments(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_appointments(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    
    
@router.get(
    "/knowledge",
    response_model=DashboardKnowledgeResponse,
)
async def dashboard_knowledge(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = DashboardService(db)

    return await service.get_knowledge_documents(
        tenant_id=tenant_id,
    )
