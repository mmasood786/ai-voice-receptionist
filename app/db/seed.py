import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Tenant


async def seed() -> None:
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Tenant).where(
                Tenant.name == "Demo Service Company"
            )
        )

        tenant = result.scalar_one_or_none()

        if tenant:
            # print(f"Tenant already exists: {tenant.id}")
            return

        tenant = Tenant(
            name="Demo Service Company",
            phone="+1-555-0100",
            email="demo@example.com",
        )

        db.add(tenant)

        await db.commit()
        await db.refresh(tenant)

        # print(f"Created tenant: {tenant.id}")


if __name__ == "__main__":
    asyncio.run(seed())