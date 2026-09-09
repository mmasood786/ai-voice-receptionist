from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.appointments import AppointmentRepository


class AppointmentService:

    def __init__(self, db: AsyncSession):
        self.repository = AppointmentRepository(db)


    async def create_pending_appointment(
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
        ):

        if start_time.tzinfo is None:
            raise ValueError("start_time must be timezone-aware")

        if end_time.tzinfo is None:
            raise ValueError("end_time must be timezone-aware")

        if end_time <= start_time:
            raise ValueError("end_time must be after start_time")

        return await self.repository.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            start_time=start_time,
            end_time=end_time,
            time_zone=time_zone,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            cal_event_type_id=cal_event_type_id,
            status="pending",
        )

    async def confirm_appointment(
        self,
        *,
        tenant_id: int,
        appointment_id: int,
        cal_booking_id: str,
    ):

        if not cal_booking_id:
            raise ValueError("cal_booking_id is required")

        return await self.repository.update_cal_booking(
            appointment_id=appointment_id,
            tenant_id=tenant_id,
            cal_booking_id=cal_booking_id,
            status="confirmed",
        )
