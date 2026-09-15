from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead
from app.repositories.leads import LeadRepository


class LeadFollowUpService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.leads = LeadRepository(db)

    def calculate_next_follow_up(
        self,
        *,
        lead_score: int,
        follow_up_count: int,
        now: datetime | None = None,
    ) -> datetime:

        if now is None:
            now = datetime.now(timezone.utc)

        # HOT
        if lead_score >= 70:
            delays = [1, 3, 7]

        # WARM
        elif lead_score >= 40:
            delays = [2, 5, 10]

        # COLD
        else:
            delays = [7, 14]

        # Maximum cadence reached
        if follow_up_count >= len(delays):
            return now

        days = delays[follow_up_count]

        return now + timedelta(days=days)

    async def schedule_follow_up(
        self,
        *,
        tenant_id: int,
        lead_id: int,
    ) -> Lead | None:

        lead = await self.leads.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        # Don't schedule follow-ups for completed/stopped leads
        if lead.follow_up_status in {
            "stopped",
            "converted",
        }:
            return lead

        next_follow_up = self.calculate_next_follow_up(
            lead_score=lead.lead_score,
            follow_up_count=lead.follow_up_count,
        )

        lead.next_follow_up_at = next_follow_up
        lead.follow_up_status = "scheduled"

        await self.db.flush()

        return lead
    
    async def complete_follow_up(
    self,
    *,
    tenant_id: int,
    lead_id: int,
    ) -> Lead | None:

        lead = await self.leads.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        # Stop conditions
        if lead.follow_up_status in {
            "stopped",
            "converted",
        }:
            return lead

        now = datetime.now(timezone.utc)

        lead.last_contacted_at = now
        lead.follow_up_count += 1

        # Calculate next follow-up
        if lead.follow_up_count >= 3:
            lead.follow_up_status = "completed"
            lead.next_follow_up_at = None
        else:
            lead.next_follow_up_at = self.calculate_next_follow_up(
                lead_score=lead.lead_score,
                follow_up_count=lead.follow_up_count,
                now=now,
            )
            lead.follow_up_status = "scheduled"

        await self.db.flush()

        return lead
    
    async def stop_follow_up(
        self,
        *,
        tenant_id: int,
        lead_id: int,
    ) -> Lead | None:

        lead = await self.leads.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        lead.follow_up_status = "stopped"
        lead.next_follow_up_at = None

        await self.db.flush()

        return lead
    
    async def mark_replied(
        self,
        *,
        tenant_id: int,
        lead_id: int,
    ) -> Lead | None:

        lead = await self.leads.get_by_id(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if lead is None:
            return None

        lead.follow_up_status = "replied"
        lead.next_follow_up_at = None

        await self.db.flush()

        return lead