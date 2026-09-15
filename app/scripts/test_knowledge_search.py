import asyncio

from app.db.database import AsyncSessionLocal
from app.services.knowledge_search_service import KnowledgeSearchService


DEV_TENANT_ID = 1


QUESTIONS = [
    "How much does a website cost?",
    "How long does a website take?",
    "Do you build websites for restaurants?",
    "What is included in the Standard package?",
    "Do you offer hosting?",
]


async def main():
    async with AsyncSessionLocal() as db:
        service = KnowledgeSearchService(db)

        for question in QUESTIONS:
            print("\n" + "=" * 70)
            print(f"QUESTION: {question}")
            print("=" * 70)

            results = await service.search(
                tenant_id=DEV_TENANT_ID,
                query=question,
                limit=3,
            )

            for index, result in enumerate(results, start=1):
                print(f"\n--- RESULT {index} ---")
                print(f"Chunk ID: {result['chunk_id']}")
                print(f"Document ID: {result['document_id']}")
                print(f"Distance: {result['distance']:.4f}")
                print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    asyncio.run(main())