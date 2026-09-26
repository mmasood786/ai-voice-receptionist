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
        try:
            print("\n========== INGEST ==========")
            print("TENANT ID:", tenant_id)
            print("TITLE:", repr(title))
            print("SOURCE:", repr(source))
            print("============================")

            # --------------------------------------------------
            # 1. Check for existing document
            # --------------------------------------------------
            existing = await self.repository.get_document_by_source(
                tenant_id=tenant_id,
                source=source,
            )

            print("EXISTING DOCUMENT:", existing)

            # --------------------------------------------------
            # 2. Delete existing document
            # --------------------------------------------------
            if existing:
                print("DELETING EXISTING DOCUMENT:", existing.id)

                deleted = await self.repository.delete_document(
                    tenant_id=tenant_id,
                    document_id=existing.id,
                )

                if not deleted:
                    raise RuntimeError(
                        f"Failed to delete existing document {existing.id}"
                    )

                # IMPORTANT
                # Make the DELETE visible before the INSERT.
                await self.db.flush()

                print("EXISTING DOCUMENT DELETED")

            # --------------------------------------------------
            # 3. Create document
            # --------------------------------------------------
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

            print("DOCUMENT CREATED:", document.id)

            # --------------------------------------------------
            # 4. Split content
            # --------------------------------------------------
            chunks = self.splitter.split_text(content)

            print("CHUNKS:", len(chunks))

            # --------------------------------------------------
            # 5. Generate embeddings
            # --------------------------------------------------
            embeddings = self.embedding_service.embed_many(chunks)

            # --------------------------------------------------
            # 6. Create chunks
            # --------------------------------------------------
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

            # --------------------------------------------------
            # 7. COMMIT
            # --------------------------------------------------
            await self.db.commit()

            print("========== INGEST COMMITTED ==========")
            print("DOCUMENT ID:", document.id)
            print("CHUNKS CREATED:", len(chunks))

            return {
                "document_id": document.id,
                "title": title,
                "source": source,
                "chunks_created": len(chunks),
            }

        except Exception:
            await self.db.rollback()
            print("INGEST FAILED -> ROLLBACK")
            raise
        
    async def update_document(
        self,
        *,
        tenant_id: int,
        document_id: int,
        title: str,
        source: str,
        content: str,
    ):
        document = await self.repository.get_document(
            tenant_id=tenant_id,
            document_id=document_id,
        )

        if document is None:
            return None

        try:
            # Update document
            document.title = title
            document.source = source
            document.content = content
            document.metadata_json = json.dumps({
                "source": source,
                "title": title,
            })

            # Delete existing chunks
            await self.repository.delete_chunks(
                tenant_id=tenant_id,
                document_id=document_id,
            )

            # Generate new chunks
            chunks = self.splitter.split_text(content)

            # Generate embeddings
            embeddings = self.embedding_service.embed_many(chunks)

            # Create new chunks
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

            await self.db.commit()

            return {
                "document_id": document.id,
                "title": document.title,
                "source": document.source,
                "chunks_created": len(chunks),
            }

        except Exception:
            await self.db.rollback()
            raise
        
    async def reindex_document(
        self,
        *,
        tenant_id: int,
        document_id: int,
    ):
        document = await self.repository.get_document(
            tenant_id=tenant_id,
            document_id=document_id,
        )

        if document is None:
            return None

        try:
            # Remove existing chunks
            await self.repository.delete_chunks(
                tenant_id=tenant_id,
                document_id=document_id,
            )

            # Split existing document content
            chunks = self.splitter.split_text(document.content)

            # Generate fresh embeddings
            embeddings = self.embedding_service.embed_many(chunks)

            # Recreate chunks
            for index, (chunk_text, embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                metadata = {
                    "source": document.source,
                    "title": document.title,
                    "chunk_index": index,
                }

                await self.repository.create_chunk(
                    tenant_id=tenant_id,
                    document_id=document.id,
                    content=chunk_text,
                    embedding=embedding,
                    metadata_json=json.dumps(metadata),
                )

            await self.db.commit()

            return {
                "document_id": document.id,
                "chunks_created": len(chunks),
            }

        except Exception:
            await self.db.rollback()
            raise