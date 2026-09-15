import json

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge import KnowledgeRepository
from app.services.embedding_service import EmbeddingService


class KnowledgeService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.embedding_service = EmbeddingService()

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                " ",
            ],
        )

    async def ingest_document(
        self,
        *,
        tenant_id: int,
        title: str,
        source: str,
        content: str,
    ):

        # Prevent duplicate ingestion
        existing = await self.repository.get_document_by_source(
            tenant_id=tenant_id,
            source=source,
        )

        if existing:
            await self.repository.delete_document(
                tenant_id=tenant_id,
                document_id=existing.id,
            )

        # Create document
        document = await self.repository.create_document(
            tenant_id=tenant_id,
            title=title,
            source=source,
            content=content,
            metadata_json=json.dumps({
                "source": source,
                "title": title,
            }),
        )

        # Split content
        chunks = self.splitter.split_text(content)

        # Generate embeddings
        embeddings = self.embedding_service.embed_many(chunks)

        # Store chunks
        for index, (chunk_text, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            metadata = {
                "source": source,
                "title": title,
                "chunk_index": index,
            }

            await self.repository.create_chunk(
                tenant_id=tenant_id,
                document_id=document.id,
                content=chunk_text,
                embedding=embedding,
                metadata_json=json.dumps(metadata),
            )

        return {
            "document_id": document.id,
            "title": title,
            "source": source,
            "chunks_created": len(chunks),
        }