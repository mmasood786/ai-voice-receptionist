from datetime import datetime

from app.integrations.calcom import CalComClient


class AvailabilityService:

    def __init__(self):
        self.calcom = CalComClient()

    async def get_available_slots(
        self,
        start: datetime,
        end: datetime,
        time_zone: str,
        event_type_id: int | None = None,
    ) -> list[dict]:

        response = await self.calcom.get_slots(
            start=start,
            end=end,
            time_zone=time_zone,
            event_type_id=event_type_id,
        )
        data = response.get("data", {})

        slots = []

        for date, date_slots in data.items():

            for slot in date_slots:

                slots.append(
                    {
                        "date": date,
                        "start": slot["start"],
                        "end": slot["end"],
                    }
                )

        return slots