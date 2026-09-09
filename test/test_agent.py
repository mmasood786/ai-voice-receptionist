import asyncio
from datetime import datetime

from app.config import get_settings
from app.integrations.calcom import CalComClient


async def main():

    settings = get_settings()

    client = CalComClient()

    start = datetime.fromisoformat(
        "2026-09-07T09:00:00+05:00"
    )

    end = datetime.fromisoformat(
        "2026-09-07T09:30:00+05:00"
    )

    print("\n========== CAL.COM BOOKING TEST ==========")

    print("Start:", start)
    print("End:", end)

    response = await client.create_booking(
        start=start,
        end=end,
        time_zone="Asia/Karachi",
        attendee_name="AI Receptionist Test",
        attendee_email="your-real-email@example.com",
        attendee_phone="+92-300-0000000",
        event_type_id=int(
            settings.cal_event_type_id
        ),
    )

    print("\nResponse:")
    print(response)

    print("\n===========================================")


if __name__ == "__main__":
    asyncio.run(main())