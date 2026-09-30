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
        # 1. Check for an existing appointment
        # ------------------------------------------

        existing_appointment = (
            await self.appointments.get_conflicting_appointment(
                tenant_id=tenant_id,
                start_time=start_time,
                end_time=end_time,
            )
        )
        
        if existing_appointment is not None:
            return {
                "success": False,
                "error": "appointment_conflict",
                "message": (
                    "An appointment already exists "
                    "during the requested time."
                ),
            }

        # ------------------------------------------
        # 2. Create booking in Cal.com
        # ------------------------------------------

        cal_response = await self.calcom.create_booking(
            start_time=start_time,
            end_time=end_time,
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
        
        cal_booking_uid = data.get("uid")

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
            cal_booking_uid=cal_booking_uid
        )

        appointment.cal_booking_id = str(cal_booking_id)

        await self.db.flush()

        return {
            "appointment": appointment,
            "cal_booking": cal_response,
        }
         
    async def cancel_booking(
        self,
        *,
        tenant_id: int,
        customer_id: int,
        conversation_id: int | None = None,
        cancellation_reason: str | None = None,
        time_zone: str = "Asia/Karachi",
    ) -> dict:
        
        appointment = await self.appointments.get_active_by_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        
        if not appointment:
            return {
                "success": False,
                "error": "appointment_not_found",
                "message": "Appointment not found.",
            }

        # appointment = await self.appointments.get_by_id(
        #     appointment_id
        # )

        # if not appointment:
        #     return {
        #         "success": False,
        #         "error": "appointment_not_found",
        #         "message": "Appointment not found.",
        #     }

        if not appointment.cal_booking_uid:
            return {
                "success": False,
                "error": "booking_uid_missing",
                "message": "This appointment cannot be cancelled because its Cal.com booking UID is missing.",
            }

        if appointment.status == "cancelled":
            return {
                "success": False,
                "error": "already_cancelled",
                "message": "This appointment is already cancelled.",
            }

        await self.calcom.cancel_booking(
            booking_uid=appointment.cal_booking_uid,
            cancellation_reason=cancellation_reason,
        )

        appointment.status = "cancelled"

        if cancellation_reason:
            appointment.cancellation_reason = cancellation_reason

        await self.db.commit()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "status": "cancelled",
            "message": "Appointment successfully cancelled.",
        }
          
    async def reschedule_booking(
        self,
        *,
        tenant_id: int,
        customer_id: int,
        conversation_id: int | None = None,
        start_time: datetime,
        end_time: datetime,
        time_zone: str,
    ) -> dict:

        # ------------------------------------------
        # 1. Validate new time
        # ------------------------------------------

        if start_time.tzinfo is None:
            raise ValueError(
                "new_start_time must be timezone-aware"
            )

        if end_time.tzinfo is None:
            raise ValueError(
                "new_end_time must be timezone-aware"
            )

        if end_time <= start_time:
            raise ValueError(
                "new_end_time must be after new_start_time"
            )

        # ------------------------------------------
        # 2. Find current appointment
        # ------------------------------------------

        old_appointment = (
            await self.appointments.get_active_by_customer(
                tenant_id=tenant_id,
                customer_id=customer_id,
                conversation_id=conversation_id,
            )
        )

        if not old_appointment:
            return {
                "success": False,
                "error": "appointment_not_found",
                "message": "No active appointment was found to reschedule.",
            }

        if not old_appointment.cal_booking_uid:
            return {
                "success": False,
                "error": "booking_uid_missing",
                "message": (
                    "The existing appointment cannot be rescheduled "
                    "because its Cal.com booking UID is missing."
                ),
            }

        # ------------------------------------------
        # 3. Don't reschedule to the same time
        # ------------------------------------------

        if (
            old_appointment.start_time == start_time
            and old_appointment.end_time == end_time
        ):
            return {
                "success": False,
                "error": "same_time",
                "message": "The new appointment time is the same as the current appointment.",
            }

        # ------------------------------------------
        # 4. Create the NEW appointment first
        # ------------------------------------------

        new_booking_result = await self.create_booking(
            tenant_id=tenant_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            start_time=start_time,
            end_time=end_time,
            time_zone=time_zone,
            customer_name=old_appointment.customer_name,
            customer_email=old_appointment.customer_email,
            customer_phone=old_appointment.customer_phone,
            cal_event_type_id=old_appointment.cal_event_type_id,
        )

        # create_booking() returns a conflict result instead
        # of throwing when the requested time is unavailable.
        if not new_booking_result.get("appointment"):
            return new_booking_result

        new_appointment = new_booking_result["appointment"]

        # ------------------------------------------
        # 5. Cancel the OLD Cal.com booking
        # ------------------------------------------

        try:
            await self.calcom.cancel_booking(
                booking_uid=old_appointment.cal_booking_uid,
                cancellation_reason="Appointment rescheduled",
            )

        except Exception as exc:
            # The new Cal.com booking was created, but the old
            # appointment could not be cancelled.
            #
            # Remove the new local appointment from this DB
            # transaction so our local DB doesn't falsely report
            # the new appointment as confirmed.
            await self.db.rollback()

            return {
                "success": False,
                "error": "old_booking_cancellation_failed",
                "message": (
                    "The new appointment was created, but the existing "
                    "appointment could not be cancelled. Please try again "
                    "or contact support."
                ),
            }

        # ------------------------------------------
        # 6. Mark OLD local appointment cancelled
        # ------------------------------------------

        old_appointment.status = "cancelled"
        old_appointment.cancellation_reason = (
            "Appointment rescheduled"
        )

        # ------------------------------------------
        # 7. Save changes
        # ------------------------------------------

        await self.db.commit()

        # ------------------------------------------
        # 8. Return safe result
        # ------------------------------------------

        return {
            "success": True,
            "status": "rescheduled",
            "message": "Appointment successfully rescheduled.",
            "old_appointment_id": old_appointment.id,
            "new_appointment_id": new_appointment.id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "time_zone": time_zone,
        }
    