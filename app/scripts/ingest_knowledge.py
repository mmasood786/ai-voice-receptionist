import asyncio
from pathlib import Path

from app.config import get_settings
from app.db.database import AsyncSessionLocal
from app.services.knowledge_service import KnowledgeService


DEV_TENANT_ID = 1

KNOWLEDGE_DIR = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "knowledge"
    / "devstudio-hub"
)




async def ingest():

    if not KNOWLEDGE_DIR.exists():
        raise RuntimeError(
            f"Knowledge directory not found: {KNOWLEDGE_DIR}"
        )

    files = sorted(KNOWLEDGE_DIR.glob("*.md"))

    if not files:
        raise RuntimeError(
            f"No Markdown files found in {KNOWLEDGE_DIR}"
        )

    print("=" * 60)
    print("KNOWLEDGE INGESTION")
    print("=" * 60)
    print(f"Tenant ID: {DEV_TENANT_ID}")
    print(f"Directory: {KNOWLEDGE_DIR}")
    print(f"Files found: {len(files)}")
    print()

    async with AsyncSessionLocal() as db:

        service = KnowledgeService(db)

        total_chunks = 0

        for file_path in files:

            print(f"Processing: {file_path.name}")

            content = file_path.read_text(
                encoding="utf-8"
            )

            result = await service.ingest_document(
                tenant_id=DEV_TENANT_ID,
                title=file_path.stem.replace("-", " ").title(),
                source=file_path.name,
                content=content,
            )

            print(
                f"  Document ID: {result['document_id']}"
            )

            print(
                f"  Chunks: {result['chunks_created']}"
            )

            total_chunks += result["chunks_created"]

        await db.commit()

    print()
    print("=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Documents: {len(files)}")
    print(f"Chunks: {total_chunks}")


if __name__ == "__main__":
    asyncio.run(ingest())