const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let message = `API request failed: ${response.status} ${response.statusText}`;

    try {
      const data = await response.json();

      if (data?.detail) {
        message = data.detail;
      }
    } catch {}

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}


export interface DashboardOverview {
  customers: number;
  leads: number;
  conversations: number;
  appointments: number;
  knowledge_documents: number;
}

export interface DashboardActivityItem {
  type: string;
  id: number;
  title: string;
  description: string | null;
  created_at: string;
}

export interface DashboardRecentActivity {
  items: DashboardActivityItem[];
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  return apiRequest<DashboardOverview>("/dashboard/overview");
}

export async function getRecentActivity(): Promise<DashboardRecentActivity> {
  return apiRequest<DashboardRecentActivity>(
    "/dashboard/recent-activity"
  );
}



export interface DashboardConversationItem {
    id: number;
    customer_id: number | null;
    status: string | null;
    channel: string | null;
    created_at: string;
    latest_message: string | null;
  }
  
  export interface DashboardConversationsResponse {
    items: DashboardConversationItem[];
    total: number;
  }
  
  export async function getDashboardConversations(
    limit = 20,
    offset = 0
  ): Promise<DashboardConversationsResponse> {
    return apiRequest<DashboardConversationsResponse>(
      `/dashboard/conversations?limit=${limit}&offset=${offset}`
    );
  }
  
  export interface DashboardLeadItem {
    id: number;
    customer_id: number | null;
    service_interest: string | null;
    urgency: string | null;
    budget: string | null;
    timeline: string | null;
    lead_score: number | null;
    status: string | null;
    created_at: string;
  }
  
  export interface DashboardLeadsResponse {
    items: DashboardLeadItem[];
    total: number;
  }
  
  export async function getDashboardLeads(
    limit = 20,
    offset = 0
  ): Promise<DashboardLeadsResponse> {
    return apiRequest<DashboardLeadsResponse>(
      `/dashboard/leads?limit=${limit}&offset=${offset}`
    );
  }
  
  export interface DashboardAppointmentItem {
    id: number;
    customer_id: number | null;
    status: string | null;
    start_time: string;
    end_time: string;
    time_zone: string | null;
    created_at: string;
  }
  
  export interface DashboardAppointmentsResponse {
    items: DashboardAppointmentItem[];
    total: number;
  }
  
  export async function getDashboardAppointments(
    limit = 20,
    offset = 0
  ): Promise<DashboardAppointmentsResponse> {
    return apiRequest<DashboardAppointmentsResponse>(
      `/dashboard/appointments?limit=${limit}&offset=${offset}`
    );
  }
  
  export interface DashboardKnowledgeItem {
    id: number;
    title: string;
    source: string;
    chunk_count: number;
  }
  
  export interface DashboardKnowledgeResponse {
    items: DashboardKnowledgeItem[];
    total: number;
  }
  
  export async function getDashboardKnowledge(): Promise<DashboardKnowledgeResponse> {
    return apiRequest<DashboardKnowledgeResponse>(
      "/dashboard/knowledge"
    );
  }


  export interface KnowledgeDocument {
    id: number;
    tenant_id: number;
    title: string;
    source: string;
    chunk_count: number;
  }
  
  export interface KnowledgeDocumentListItem {
    id: number;
    title: string;
    source: string;
    chunk_count: number;
  }
  


  export type KnowledgeDocumentListResponse =
  KnowledgeDocumentListItem[];
  
  export interface KnowledgeDocumentCreateResponse {
    document_id: number;
    title: string;
    source: string;
    chunks_created: number;
  }
  
  export async function getKnowledgeDocuments(): Promise<KnowledgeDocumentListResponse> {
    return apiRequest<KnowledgeDocumentListResponse>(
      "/knowledge/documents"
    );
  }



  export interface KnowledgeDocumentPayload {
    title: string;
    source: string;
    content: string;
    metadata?: Record<string, unknown>;
  }
  
  export interface KnowledgeDocumentCreateResponse {
    document_id: number;
    title: string;
    source: string;
    chunks_created: number;
  }
  
  export async function createKnowledgeDocument(
    payload: KnowledgeDocumentPayload
  ): Promise<KnowledgeDocumentCreateResponse> {
    return apiRequest<KnowledgeDocumentCreateResponse>(
      "/knowledge/documents",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }
  
  export async function updateKnowledgeDocument(
    documentId: number,
    payload: KnowledgeDocumentPayload
  ): Promise<KnowledgeDocumentCreateResponse> {
    return apiRequest<KnowledgeDocumentCreateResponse>(
      `/knowledge/documents/${documentId}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      }
    );
  }
  
  export async function reindexKnowledgeDocument(
    documentId: number
  ): Promise<KnowledgeDocumentCreateResponse> {
    return apiRequest<KnowledgeDocumentCreateResponse>(
      `/knowledge/documents/${documentId}/reindex`,
      {
        method: "POST",
      }
    );
  }
  
  export async function deleteKnowledgeDocument(
    documentId: number
  ): Promise<void> {
    await apiRequest<void>(
      `/knowledge/documents/${documentId}`,
      {
        method: "DELETE",
      }
    );
  }

  export interface KnowledgeDocumentDetail {
    id: number;
    tenant_id: number;
    title: string;
    source: string;
    content: string;
    chunk_count: number;
  }
  
  export async function getKnowledgeDocument(
    documentId: number
  ): Promise<KnowledgeDocumentDetail> {
    return apiRequest<KnowledgeDocumentDetail>(
      `/knowledge/documents/${documentId}`
    );
  }



  export interface LoginRequest {
    email: string;
    password: string;
  }
  
  export interface AuthUser {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    created_at: string;
  }
  
  export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: AuthUser;
  }
  
  export async function login(
    payload: LoginRequest
  ): Promise<LoginResponse> {
    return apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }