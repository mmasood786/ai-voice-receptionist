from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeDocument, KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self,
        *,
        tenant_id: int,
        title: str,
        source: str,
        content: str,
        metadata_json: str | None = None,
    ):
        document = KnowledgeDocument(
            tenant_id=tenant_id,
            title=title,
            source=source,
            content=content,
            metadata_json=metadata_json,
        )

        self.db.add(document)
        await self.db.flush()
        return document

    async def create_chunk(
        self,
        *,
        tenant_id: int,
        document_id: int,
        content: str,
        embedding: list[float],
        metadata_json: str | None = None,
    ):
        chunk = KnowledgeChunk(
            tenant_id=tenant_id,
            document_id=document_id,
            content=content,
            embedding=embedding,
            metadata_json=metadata_json,
        )

        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def get_document_by_source(
        self,
        *,
        tenant_id: int,
        source: str,
    ):
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.source == source,
            )
        )

        return result.scalar_one_or_none()

    async def delete_document(
        self,
        *,
        tenant_id: int,
        source: str,
    ):
        document = await self.get_document_by_source(
            tenant_id=tenant_id,
            source=source,
        )

        if document:
            await self.db.delete(document)
            await self.db.flush()

    async def search_similar(
        self,
        *,
        tenant_id: int,
        query_embedding: list[float],
        limit: int = 5,
    ):
        """
        Semantic vector search using cosine distance.

        Lower distance = more similar.
        """

        distance = KnowledgeChunk.embedding.cosine_distance(
            query_embedding
        )

        result = await self.db.execute(
            select(
                KnowledgeChunk,
                distance.label("distance"),
            )
            .where(
                KnowledgeChunk.tenant_id == tenant_id,
                KnowledgeChunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(limit)
        )

        return result.all()