from typing import Any

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from zoneinfo import ZoneInfo

settings = get_settings()


class CalComClient:
    BASE_URL = "https://api.cal.com/v2"

    SLOTS_API_VERSION = "2024-09-04"
    BOOKINGS_API_VERSION = "2026-05-01"
    EVENT_TYPES_API_VERSION = "2024-06-14"

    def __init__(self):
        self.auth_headers = {
            "Authorization": f"Bearer {settings.cal_api_key}",
            "Content-Type": "application/json",
        }

    # keep your existing get_slots(), get_bookings(),
    # get_event_type(), get_event_types() methods

    async def create_booking(
        self,
        *,
        start_time: datetime,
        end_time: datetime,
        time_zone: str,
        attendee_name: str,
        attendee_email: str,
        event_type_id: int | None = None,
        attendee_phone: str | None = None,
    ) -> dict:

        if start_time.tzinfo is None:
            raise ValueError("start must be timezone-aware")

        if end_time.tzinfo is None:
            raise ValueError("end must be timezone-aware")

        if end_time <= start_time:
            raise ValueError("end must be after start")

        event_type_id = (
            event_type_id
            if event_type_id is not None
            else int(settings.cal_event_type_id)
        )

        start_utc = (
            start_time.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        payload = {
            "start": start_utc,
            "eventTypeId": event_type_id,
            "attendee": {
                "name": attendee_name,
                "email": attendee_email,
                "timeZone": time_zone,
            },
        }

        if attendee_phone:
            payload["attendee"]["phoneNumber"] = attendee_phone

        headers = {
            **self.auth_headers,
            "cal-api-version": "2026-02-25",
        }

        print("\n========== CAL.COM CREATE BOOKING ==========")
        print("Payload:")
        print(payload)
        print("Headers:")
        print({
            "cal-api-version": headers["cal-api-version"]
        })

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/bookings",
                headers=headers,
                json=payload,
            )

        print("\nStatus:", response.status_code)
        print("Response:", response.text)
        print("============================================\n")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Cal.com booking failed "
                f"({response.status_code}): {response.text}"
            )

        return response.json()

    async def get_slots(
    self,
    start_time: datetime,
    end_time: datetime,
    time_zone: str,
    event_type_id: int | None = None,
    duration: int | None = None,
    ) -> dict:

        if start_time.tzinfo is None:
            raise ValueError("start must be timezone-aware")

        if end_time.tzinfo is None:
            raise ValueError("end must be timezone-aware")

        if end_time <= start_time:
            raise ValueError("end must be after start")

        try:
            ZoneInfo(time_zone)
        except Exception:
            raise ValueError(
                f"Invalid timezone: {time_zone}"
            )

        event_type_id = (
            event_type_id
            if event_type_id is not None
            else int(settings.cal_event_type_id)
        )

        params = {
            "eventTypeId": event_type_id,
            "start": (
                start_time
                .astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            ),
            "end": (
                end_time
                .astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            ),
            "timeZone": time_zone,
            "format": "range",
        }

        if duration is not None:
            params["duration"] = duration

        headers = {
            **self.auth_headers,
            "cal-api-version": self.SLOTS_API_VERSION,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/slots",
                headers=headers,
                params=params,
            )
        
        print("\n========== CAL.COM GET SLOTS ==========")
        print("Status:", response.status_code)
        print("Params:")
        print(params)
        print("Response:")
        print(response.text)
        print("=======================================\n")
        if response.status_code >= 400:
            raise RuntimeError(
                f"Cal.com slots failed "
                f"({response.status_code}): {response.text}"
            )


        response.raise_for_status()

        return response.json()

    async def get_event_types(self) -> dict:
        headers = {
            **self.auth_headers,
            "cal-api-version": self.EVENT_TYPES_API_VERSION,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/event-types",
                headers=headers,
            )

        response.raise_for_status()

        return response.json()

    async def get_event_type(
        self,
        event_type_id: int,
    ) -> dict:

        headers = {
            **self.auth_headers,
            "cal-api-version": self.EVENT_TYPES_API_VERSION,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/event-types/{event_type_id}",
                headers=headers,
            )

        response.raise_for_status()

        return response.json()
      
    async def cancel_booking(
        self,
        *,
        booking_uid: str,
        cancellation_reason: str | None = None,
    ) -> dict:

        if not booking_uid:
            raise ValueError("booking_uid is required")

        payload = {}

        if cancellation_reason:
            payload["cancellationReason"] = cancellation_reason

        headers = {
            **self.auth_headers,
            # "cal-api-version": self.BOOKINGS_API_VERSION,
            "cal-api-version": settings.cal_api_version,
            "Content-Type": "application/json",
        }

        print("\n========== CAL.COM CANCEL BOOKING ==========")
        print("Booking UID:", booking_uid)
        print("BOOKING API Version:", self.BOOKINGS_API_VERSION)
        print("CAL API Version:", settings.cal_api_version)
        print("Payload:", payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/bookings/{booking_uid}/cancel",
                headers=headers,
                json=payload,
            )

        print("Status:", response.status_code)
        print("Response:", response.text)
        print("============================================\n")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Cal.com cancellation failed "
                f"({response.status_code}): {response.text}"
            )

        return response.json()
    
    
    
