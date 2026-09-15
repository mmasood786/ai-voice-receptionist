import asyncio

from app.db.database import AsyncSessionLocal
from app.services.rag_service import RAGService


DEV_TENANT_ID = 1


QUESTIONS = [
    "How much does a website cost?",
    "How long does a website take?",
    "What is included in the Standard package?",
    "Do you build websites for restaurants?",
    "Do you offer hosting?",
    "Do you provide AI automation services?",
]


async def main():

    async with AsyncSessionLocal() as db:

        rag = RAGService(db)

        for question in QUESTIONS:

            print("\n" + "=" * 80)
            print(f"QUESTION: {question}")
            print("=" * 80)

            try:
                answer = await rag.answer(
                    tenant_id=DEV_TENANT_ID,
                    question=question,
                )

                print("\nANSWER:")
                print(answer)

            except Exception as exc:
                print("\nRAG ERROR:")
                print(repr(exc))


if __name__ == "__main__":
    asyncio.run(main())