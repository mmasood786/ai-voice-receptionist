from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead
from app.repositories.leads import LeadRepository

from app.services.lead_scoring import (
    calculate_lead_score,
    get_lead_status,
)

class LeadService:
    def __init__(self, db: AsyncSession):
        self.repository = LeadRepository(db)

    async def create_lead(
        self,
        tenant_id: int,
        customer_id: int | None,
        name: str,
        phone: str,
        email: str | None = None,
        notes: str | None = None,
    ) -> Lead:

        existing = await self.repository.get_by_phone(
            tenant_id=tenant_id,
            phone=phone,
        )

        if existing:
            return existing

        return await self.repository.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            name=name,
            phone=phone,
            email=email,
            notes=notes,
        )

    async def get_lead(
        self,
        tenant_id: int,
        lead_id: int,
    ) -> Lead | None:
        return await self.repository.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

    async def update_lead(
        self,
        tenant_id: int,
        lead_id: int,
        **fields,
    ) -> Lead | None:

        lead = await self.repository.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        return await self.repository.update(
            lead=lead,
            **fields,
        )
        
        
    async def qualify_lead(
        self,
        *,
        tenant_id: int,
        lead_id: int,
        service_interest: str | None,
        urgency: str | None,
        budget: str | None,
        timeline: str | None,
    ):
        score = calculate_lead_score(
            service_interest=service_interest,
            urgency=urgency,
            budget=budget,
            timeline=timeline,
        )

        status = get_lead_status(score)

        lead = await self.repository.update_qualification(
            tenant_id=tenant_id,
            lead_id=lead_id,
            service_interest=service_interest,
            urgency=urgency,
            budget=budget,
            timeline=timeline,
            lead_score=score,
            status=status,
        )

        return lead
        