from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentListItem,
    KnowledgeDocumentResponse,
)
from app.services.knowledge_service import (
    KnowledgeService,
)
from app.repositories.knowledge import KnowledgeRepository
from app.api.dependencies.tenant import get_current_tenant_id

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
)



class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)


class KnowledgeDocumentResponse(BaseModel):
    document_id: int
    title: str
    source: str
    chunks_created: int

class KnowledgeDocumentDetailResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    source: str
    chunk_count: int




@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_document(
    request: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):

    service = KnowledgeService(db)

    document = await service.ingest_document(
        tenant_id=tenant_id,
        title=request.title,
        content=request.content,
        source=request.source,
    )

    
    return document

@router.get(
    "/documents",
    response_model=list[KnowledgeDocumentListItem],
)
async def list_knowledge_documents(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    repository = KnowledgeRepository(db)

    rows = await repository.list_documents(
        tenant_id=tenant_id,
    )

    return [
        {
            "id": document.id,
            "title": document.title,
            "source": document.source,
            "chunk_count": chunk_count,
        }
        for document, chunk_count in rows
    ]


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
)
async def get_knowledge_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    repository = KnowledgeRepository(db)

    document = await repository.get_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    chunk_count = await repository.get_chunk_count(
        tenant_id=tenant_id,
        document_id=document.id,
    )

    return KnowledgeDocumentDetailResponse(
        id=document.id,
        tenant_id=document.tenant_id,
        title=document.title,
        source=document.source,
        content=document.content,
        chunk_count=chunk_count,
    )

@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    repository = KnowledgeRepository(db)

    deleted = await repository.delete_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    await db.commit()
    
    
@router.put(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
)
async def update_knowledge_document(
    document_id: int,
    request: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = KnowledgeService(db)

    result = await service.update_document(
        tenant_id=tenant_id,
        document_id=document_id,
        title=request.title,
        source=request.source,
        content=request.content,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    return result


@router.post(
    "/documents/{document_id}/reindex",
)
async def reindex_knowledge_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    service = KnowledgeService(db)

    result = await service.reindex_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    return result
