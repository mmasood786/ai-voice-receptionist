from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead


class LeadRepository:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(
        self,
        *,
        tenant_id: int,
        customer_id: int | None,
        name: str,
        phone: str,
        email: str | None = None,
        notes: str | None = None,
        service_interest: str | None = None,
        urgency: str | None = None,
        budget: str | None = None,
        timeline: str | None = None,
    ) -> Lead:

        lead = Lead(
            tenant_id=tenant_id,
            customer_id=customer_id,
            name=name,
            phone=phone,
            email=email,
            notes=notes,
            service_interest=service_interest,
            urgency=urgency,
            budget=budget,
            timeline=timeline,
            lead_score=0,
            status="new",
        )

        self.db.add(lead)

        await self.db.flush()

        return lead
    
    async def update_qualification(
    self,
    *,
    tenant_id: int,
    lead_id: int,
    service_interest: str | None,
    urgency: str | None,
    budget: str | None,
    timeline: str | None,
    lead_score: int,
    status: str,
    ) -> Lead | None:

        lead = await self.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        lead.service_interest = service_interest
        lead.urgency = urgency
        lead.budget = budget
        lead.timeline = timeline
        lead.lead_score = lead_score
        lead.status = status

        await self.db.flush()

        return lead

    async def get_by_id(
        self,
        tenant_id: int,
        lead_id: int,
    ) -> Lead | None:

        result = await self.db.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        tenant_id: int,
        phone: str,
    ) -> Lead | None:

        result = await self.db.execute(
            select(Lead).where(
                Lead.tenant_id == tenant_id,
                Lead.phone == phone,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        lead: Lead,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> Lead:

        if name is not None:
            lead.name = name

        if phone is not None:
            lead.phone = phone

        if email is not None:
            lead.email = email

        if status is not None:
            lead.status = status

        if notes is not None:
            lead.notes = notes

        await self.db.flush()

        return lead
