from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.customers import CustomerRepository

class CustomerService:

    def __init__(self, db):
        self.db = db
        self.customers = CustomerRepository(db)

    async def resolve_customer(
        self,
        *,
        tenant_id: int,
        phone: str,
        email: str | None = None,
    ) -> dict:

        phone_matches = await self.customers.get_by_phone(
            tenant_id=tenant_id,
            phone=phone,
        )

        # No customer with this phone
        if not phone_matches:
            return {
                "status": "new_customer",
                "customer": None,
                "matches": [],
            }

        # We have email, so first look for exact phone + email.
        if email:
            exact_match = await self.customers.get_by_phone_and_email(
                tenant_id=tenant_id,
                phone=phone,
                email=email,
            )

            if exact_match:
                return {
                    "status": "exact_match",
                    "customer": exact_match,
                    "matches": phone_matches,
                }

            # Same phone but different email.
            return {
                "status": "possible_conflict",
                "customer": None,
                "matches": phone_matches,
            }

        # Phone exists but no email was provided.
        return {
            "status": "possible_conflict",
            "customer": None,
            "matches": phone_matches,
        }

    async def create_customer(
        self,
        *,
        tenant_id: int,
        name: str,
        phone: str,
        email: str | None = None,
    ):

        return await self.customers.create(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
        )