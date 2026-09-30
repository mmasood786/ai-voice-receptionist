from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment


class AppointmentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        tenant_id: int,
        customer_id: int | None,
        conversation_id: int | None,
        start_time: datetime,
        end_time: datetime,
        time_zone: str,
        customer_name: str,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        cal_event_type_id: int | None = None,
        status: str = "pending",
        cal_booking_uid: str | None = None,
    ) -> Appointment:

        appointment = Appointment(
            tenant_id=tenant_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            cal_event_type_id=cal_event_type_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            time_zone=time_zone,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            cal_booking_uid=cal_booking_uid
        )

        self.db.add(appointment)

        await self.db.flush()

        return appointment

    async def get_by_id(
        self,
        appointment_id: int,
        tenant_id: int,
    ) -> Appointment | None:

        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_cal_booking_id(
        self,
        cal_booking_id: str,
        tenant_id: int,
    ) -> Appointment | None:

        result = await self.db.execute(
            select(Appointment).where(
                Appointment.cal_booking_id == cal_booking_id,
                Appointment.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()

    async def update_cal_booking(
        self,
        appointment_id: int,
        tenant_id: int,
        cal_booking_id: str,
        status: str = "confirmed",
    ) -> Appointment | None:

        appointment = await self.get_by_id(
            appointment_id=appointment_id,
            tenant_id=tenant_id,
        )

        if appointment is None:
            return None

        appointment.cal_booking_id = cal_booking_id
        appointment.status = status

        await self.db.flush()

        return appointment
    
    async def get_conflicting_appointment(
        self,
        *,
        tenant_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> Appointment | None:

        result = await self.db.execute(
            select(Appointment).where(
                Appointment.tenant_id == tenant_id,
                Appointment.start_time < end_time,
                Appointment.end_time > start_time,
                Appointment.status.notin_(
                    ["cancelled", "canceled"]
                ),
            ).limit(1)
        )

        return result.scalar_one_or_none()
    
    
    async def get_active_by_customer(
        self,
        *,
        tenant_id: int,
        customer_id: int,
        conversation_id: int | None = None,
    ):
        query = (
            select(Appointment)
            .where(
                Appointment.tenant_id == tenant_id,
                Appointment.customer_id == customer_id,
                Appointment.status == "confirmed",
            )
            .order_by(Appointment.start_time.asc())
        )

        if conversation_id is not None:
            query = query.where(
                Appointment.conversation_id == conversation_id
            )

        result = await self.db.execute(query)
        appointments = result.scalars().all()
        
        if len(appointments) == 0:
            return None

        if len(appointments) > 1:
            raise ValueError("multiple_active_appointments")

        return appointments[0]