from app.services.knowledge_search_service import KnowledgeSearchService
from app.agents.provider import groq_model
from agents import Agent, Runner


class RAGService:
    def __init__(self, db):
        self.db = db
        self.knowledge_search = KnowledgeSearchService(db)

    async def answer(
        self,
        *,
        tenant_id: int,
        question: str,
        limit: int = 4,
    ) -> str:

        results = await self.knowledge_search.search(
            tenant_id=tenant_id,
            query=question,
            limit=limit,
        )

        if not results:
            return (
                "I’m sorry, but I don’t have that information available "
                "right now."
            )

        context_parts = []

        for result in results:
            context_parts.append(
                f"[Knowledge Chunk {result['chunk_id']}]\n"
                f"{result['content']}"
            )

        context = "\n\n".join(context_parts)

        agent = Agent(
            name="RAG Knowledge Assistant",
            model=groq_model,
            instructions="""
                                You answer customer questions using ONLY the supplied knowledge base.

                                RULES:
                                - Use only information contained in the knowledge context.
                                - Never invent prices, services, policies, timelines, or features.
                                - If the answer is not supported by the context, say that you don't
                                have that information available.
                                - Do not mention embeddings, vector search, chunks, databases,
                                retrieval, or internal systems.
                                - Be concise, professional, friendly, and natural.
                                - Answer the customer's actual question directly.
                         """,
                                        )

        prompt = f"""
                        KNOWLEDGE CONTEXT:

                        {context}

                        CUSTOMER QUESTION:

                        {question}

                        Answer the customer's question using only the knowledge context.
                  """

        result = await Runner.run(
            agent,
            prompt,
        )

        return result.final_output