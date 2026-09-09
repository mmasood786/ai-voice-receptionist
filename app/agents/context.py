# from dataclasses import dataclass

# @dataclass
# class AgentContext:
#     tenant_id: int
#     conversation_id: int
#     customer_id: int | None = None
#     lead_id: int | None = None
    
from datetime import datetime
from zoneinfo import ZoneInfo

class AgentContext:
    def __init__(
        self,
        tenant_id: int,
        conversation_id: int,
        customer_id: int | None = None,
        lead_id: int | None = None,
        time_zone: str = "Asia/Karachi",
    ):
        self.tenant_id = tenant_id
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.lead_id = lead_id
        self.time_zone = time_zone

    @property
    def current_datetime(self) -> datetime:
        return datetime.now(ZoneInfo(self.time_zone))