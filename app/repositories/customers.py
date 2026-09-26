from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer


class CustomerRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        *,
        tenant_id: int,
        customer_id: int,
    ) -> Customer | None:

        result = await self.db.execute(
            select(Customer)
            .where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        *,
        tenant_id: int,
        phone: str,
    ) -> list[Customer]:

        result = await self.db.execute(
            select(Customer)
            .where(
                Customer.tenant_id == tenant_id,
                Customer.phone == phone,
            )
            .order_by(Customer.id.asc())
        )

        return list(result.scalars().all())

    async def get_by_email(
        self,
        *,
        tenant_id: int,
        email: str,
    ) -> list[Customer]:

        result = await self.db.execute(
            select(Customer)
            .where(
                Customer.tenant_id == tenant_id,
                Customer.email == email,
            )
            .order_by(Customer.id.asc())
        )

        return list(result.scalars().all())

    async def get_by_phone_and_email(
        self,
        *,
        tenant_id: int,
        phone: str,
        email: str,
    ) -> Customer | None:

        result = await self.db.execute(
            select(Customer)
            .where(
                Customer.tenant_id == tenant_id,
                Customer.phone == phone,
                Customer.email == email,
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_id: int,
        name: str,
        phone: str,
        email: str | None = None,
    ) -> Customer:

        customer = Customer(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
        )

        self.db.add(customer)
        await self.db.flush()

        return customer