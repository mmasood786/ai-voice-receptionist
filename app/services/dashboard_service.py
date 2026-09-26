from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer, Lead, Conversation, Appointment, KnowledgeDocument, Message, KnowledgeChunk


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(
        self,
        *,
        tenant_id: int,
    ) -> dict:
        customers_result = await self.db.execute(
            select(func.count(Customer.id)).where(
                Customer.tenant_id == tenant_id
            )
        )

        leads_result = await self.db.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == tenant_id
            )
        )

        conversations_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.tenant_id == tenant_id
            )
        )

        appointments_result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.tenant_id == tenant_id
            )
        )

        documents_result = await self.db.execute(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.tenant_id == tenant_id
            )
        )

        return {
            "customers": customers_result.scalar_one(),
            "leads": leads_result.scalar_one(),
            "conversations": conversations_result.scalar_one(),
            "appointments": appointments_result.scalar_one(),
            "knowledge_documents": documents_result.scalar_one(),
        }

    async def get_recent_activity(
        self,
        *,
        tenant_id: int,
        limit: int = 10,
    ) -> list[dict]:

        activities = []

        # Recent conversations
        conversations_result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id
            )
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )

        conversations = conversations_result.scalars().all()

        for conversation in conversations:
            activities.append({
                "type": "conversation",
                "id": conversation.id,
                "title": "New conversation",
                "description": f"Conversation #{conversation.id}",
                "created_at": conversation.created_at,
            })

        # Recent leads
        leads_result = await self.db.execute(
            select(Lead)
            .where(
                Lead.tenant_id == tenant_id
            )
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )

        leads = leads_result.scalars().all()

        for lead in leads:
            activities.append({
                "type": "lead",
                "id": lead.id,
                "title": "Lead created",
                "description": f"Lead #{lead.id}",
                "created_at": lead.created_at,
            })

        # Recent appointments
        appointments_result = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.tenant_id == tenant_id
            )
            .order_by(Appointment.created_at.desc())
            .limit(limit)
        )

        appointments = appointments_result.scalars().all()

        for appointment in appointments:
            activities.append({
                "type": "appointment",
                "id": appointment.id,
                "title": "Appointment created",
                "description": f"Appointment #{appointment.id}",
                "created_at": appointment.created_at,
            })

        activities.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )

        return activities[:limit]
    
    async def get_conversations(
        self,
        *,
        tenant_id: int,
        limit: int = 20,
        offset: int = 0,
    ):
        total_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.tenant_id == tenant_id
            )
        )

        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id
            )
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        conversations = result.scalars().all()

        items = []

        for conversation in conversations:
            message_result = await self.db.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation.id
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )

            latest_message = message_result.scalar_one_or_none()

            items.append({
                "id": conversation.id,
                "customer_id": conversation.customer_id,
                "status": conversation.status,
                "channel": conversation.channel,
                "created_at": conversation.created_at,
                "latest_message": (
                    latest_message.content
                    if latest_message
                    else None
                ),
            })

        return {
            "items": items,
            "total": total,
        }
        
    async def get_leads(
        self,
        *,
        tenant_id: int,
        limit: int = 20,
        offset: int = 0,
    ):
        total_result = await self.db.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == tenant_id
            )
        )

        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Lead)
            .where(
                Lead.tenant_id == tenant_id
            )
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        leads = result.scalars().all()

        items = [
            {
                "id": lead.id,
                "customer_id": lead.customer_id,
                "service_interest": lead.service_interest,
                "urgency": lead.urgency,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "lead_score": lead.lead_score,
                "status": lead.status,
                "created_at": lead.created_at,
            }
            for lead in leads
        ]

        return {
            "items": items,
            "total": total,
        }
         
    async def get_appointments(
        self,
        *,
        tenant_id: int,
        limit: int = 20,
        offset: int = 0,
    ):
        total_result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.tenant_id == tenant_id
            )
        )

        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.tenant_id == tenant_id
            )
            .order_by(Appointment.start_time.desc())
            .offset(offset)
            .limit(limit)
        )

        appointments = result.scalars().all()

        items = [
            {
                "id": appointment.id,
                "customer_id": appointment.customer_id,
                "status": appointment.status,
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,
                "time_zone": appointment.time_zone,
                "created_at": appointment.created_at,
            }
            for appointment in appointments
        ]

        return {
            "items": items,
            "total": total,
        }
        
    async def get_knowledge_documents(
        self,
        *,
        tenant_id: int,
    ):
        result = await self.db.execute(
            select(
                KnowledgeDocument,
                func.count(KnowledgeChunk.id).label("chunk_count"),
            )
            .outerjoin(
                KnowledgeChunk,
                KnowledgeChunk.document_id == KnowledgeDocument.id,
            )
            .where(
                KnowledgeDocument.tenant_id == tenant_id
            )
            .group_by(KnowledgeDocument.id)
            .order_by(KnowledgeDocument.id.desc())
        )

        rows = result.all()

        return {
            "items": [
                {
                    "id": document.id,
                    "title": document.title,
                    "source": document.source,
                    "chunk_count": chunk_count,
                }
                for document, chunk_count in rows
            ],
            "total": len(rows),
        }