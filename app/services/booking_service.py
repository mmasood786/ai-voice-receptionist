from datetime import datetime

from app.integrations.calcom import CalComClient
from app.repositories.appointments import AppointmentRepository


class BookingService:

    def __init__(self, db):
        self.db = db
        self.calcom = CalComClient()
        self.appointments = AppointmentRepository(db)

    async def create_booking(
        self,
        *,
        tenant_id: int,
        customer_id: int | None,
        conversation_id: int | None,
        start_time: datetime,
        end_time: datetime,
        time_zone: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str | None = None,
        cal_event_type_id: int | None = None,
    ):

        if start_time.tzinfo is None:
            raise ValueError(
                "start_time must be timezone-aware"
            )

        if end_time.tzinfo is None:
            raise ValueError(
                "end_time must be timezone-aware"
            )

        if end_time <= start_time:
            raise ValueError(
                "end_time must be after start_time"
            )

        # ------------------------------------------
        # 1. Create booking in Cal.com
        # ------------------------------------------

        cal_response = await self.calcom.create_booking(
            start=start_time,
            end=end_time,
            time_zone=time_zone,
            attendee_name=customer_name,
            attendee_email=customer_email,
            attendee_phone=customer_phone,
            event_type_id=cal_event_type_id,
        )

        # ------------------------------------------
        # 2. Extract Cal.com booking ID
        # ------------------------------------------

        data = cal_response.get("data", {})

        cal_booking_id = (
            data.get("id")
            or data.get("bookingId")
        )

        if not cal_booking_id:
            raise RuntimeError(
                "Cal.com booking succeeded but no booking ID was returned"
            )

        # ------------------------------------------
        # 3. Save application appointment
        # ------------------------------------------

        appointment = await self.appointments.create(
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
            status="confirmed",
        )

        appointment.cal_booking_id = str(cal_booking_id)

        await self.db.flush()

        return {
            "appointment": appointment,
            "cal_booking": cal_response,
        }