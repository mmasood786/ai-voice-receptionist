from pydantic import BaseModel, Field


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source: str | None = Field(default=None, max_length=500)


class KnowledgeDocumentResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    source: str
    content: str
    chunk_count: int

    model_config = {
        "from_attributes": True,
    }


class KnowledgeDocumentListItem(BaseModel):
    id: int
    title: str
    source: str | None
    chunk_count: int