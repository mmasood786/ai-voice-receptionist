from datetime import datetime
from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    customers: int
    leads: int
    conversations: int
    appointments: int
    knowledge_documents: int

class DashboardActivityItem(BaseModel):
    type: str
    id: int
    title: str
    description: str | None = None
    created_at: datetime

class DashboardRecentActivityResponse(BaseModel):
    items: list[DashboardActivityItem]
 
 
      
class DashboardConversationItem(BaseModel):
    id: int
    customer_id: int | None
    status: str | None
    channel: str | None
    created_at: datetime
    latest_message: str | None

class DashboardConversationsResponse(BaseModel):
    items: list[DashboardConversationItem]
    total: int
  
    
    
class DashboardLeadItem(BaseModel):
    id: int
    customer_id: int | None
    service_interest: str | None
    urgency: str | None
    budget: str | None
    timeline: str | None
    lead_score: int | None
    status: str | None
    created_at: datetime

class DashboardLeadsResponse(BaseModel):
    items: list[DashboardLeadItem]
    total: int
    
   
    
class DashboardAppointmentItem(BaseModel):
    id: int
    customer_id: int | None
    status: str | None
    start_time: datetime
    end_time: datetime
    time_zone: str | None
    created_at: datetime

class DashboardAppointmentsResponse(BaseModel):
    items: list[DashboardAppointmentItem]
    total: int
    
    
    
class DashboardKnowledgeItem(BaseModel):
    id: int
    title: str
    source: str
    chunk_count: int

class DashboardKnowledgeResponse(BaseModel):
    items: list[DashboardKnowledgeItem]
    total: int