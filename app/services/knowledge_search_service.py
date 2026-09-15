from app.repositories.knowledge import KnowledgeRepository
from app.services.embedding_service import EmbeddingService


class KnowledgeSearchService:
    def __init__(self, db):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        *,
        tenant_id: int,
        query: str,
        limit: int = 5,
    ):
        # Convert user's question into a 384-dimensional vector
        query_embedding = self.embedding_service.embed(query)
        
       
        

        # Search Neon using pgvector
        results = await self.repository.search_similar(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            limit=limit,
        )
        
        

        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "distance": float(distance),
            }
            for chunk, distance in results
        ]