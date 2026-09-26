import json

from sqlalchemy import delete, select, func,  text
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
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.source == source,
            )
            .limit(1)
        )

        document = result.scalar_one_or_none()

        return document
    
    async def get_document(
        self,
        *,
        tenant_id: int,
        document_id: int,
    ):
        result = await self.db.execute(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
        )

        document = result.scalar_one_or_none()

        return document
    
    async def delete_document(
        self,
        *,
        tenant_id: int,
        document_id: int,
    ):
        document = await self.get_document(
            tenant_id=tenant_id,
            document_id=document_id,
        )

        if document is None:
            return False

        # Delete chunks first
        await self.db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.tenant_id == tenant_id,
            )
        )

        # Delete document
        await self.db.delete(document)

        await self.db.flush()

        return True

    async def search_similar(
        self,
        *,
        tenant_id: int,
        query_embedding: list[float],
        limit: int = 5,
        max_distance: float = 0.45,
    ):
        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

        result = await self.db.execute(
            select(
                KnowledgeChunk,
                distance.label("distance"),
            )
            .where(
                KnowledgeChunk.tenant_id == tenant_id,
                KnowledgeChunk.embedding.is_not(None),
                distance <= max_distance,
            )
            .order_by(distance)
            .limit(limit)
        )

        return result.all()

    async def list_documents(
        self,
        *,
        tenant_id: int,
    ) -> list[tuple[KnowledgeDocument, int]]:

        stmt = (
            select(
                KnowledgeDocument,
                func.count(KnowledgeChunk.id).label("chunk_count"),
            )
            .outerjoin(
                KnowledgeChunk,
                KnowledgeChunk.document_id == KnowledgeDocument.id,
            )
            .where(
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .group_by(KnowledgeDocument.id)
            .order_by(KnowledgeDocument.id.desc())
        )

        result = await self.db.execute(stmt)

        return result.all()

    async def get_chunk_count(
        self,
        *,
        tenant_id: int,
        document_id: int,
    ) -> int:

        result = await self.db.execute(
            select(func.count(KnowledgeChunk.id))
            .where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.tenant_id == tenant_id,
            )
        )

        return result.scalar_one()
    
    async def delete_chunks(
        self,
        *,
        tenant_id: int,
        document_id: int,
    ):
        result = await self.db.execute(
            select(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.tenant_id == tenant_id,
            )
        )

        chunks = result.scalars().all()

        for chunk in chunks:
            await self.db.delete(chunk)

        return len(chunks)


    

