# import asyncio

# from sqlalchemy import select

# from app.db.database import AsyncSessionLocal
# from app.db.models import Tenant


# async def seed() -> None:
#     async with AsyncSessionLocal() as db:

#         result = await db.execute(
#             select(Tenant).where(
#                 Tenant.name == "Demo Service Company"
#             )
#         )

#         tenant = result.scalar_one_or_none()

#         if tenant:
#             # print(f"Tenant already exists: {tenant.id}")
#             return

#         tenant = Tenant(
#             name="Demo Service Company",
#             phone="+1-555-0100",
#             email="demo@example.com",
#         )

#         db.add(tenant)

#         await db.commit()
#         await db.refresh(tenant)

#         # print(f"Created tenant: {tenant.id}")


# if __name__ == "__main__":
#     asyncio.run(seed())


from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.db.database import AsyncSessionLocal
from app.db.models import (
    Appointment,
    Customer,
    Lead,
    Review,
    Tenant,
)


DEV_TENANT_ID = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def seed():
    async with AsyncSessionLocal() as db:

        # ---------------------------------------------------------
        # 1. TENANT
        # ---------------------------------------------------------
        tenant = await db.get(Tenant, DEV_TENANT_ID)

        if tenant is None:
            tenant = Tenant(
                id=DEV_TENANT_ID,
                name="Demo Service Company",
            )
            db.add(tenant)
            await db.flush()
            print("Created tenant: Demo Service Company")
        else:
            print(f"Tenant already exists: {tenant.name}")

        # ---------------------------------------------------------
        # 2. CUSTOMERS
        # ---------------------------------------------------------
        customer_data = [
            {
                "name": "Ali Khan",
                "phone": "+923001111111",
                "email": "ali@example.com",
            },
            {
                "name": "Sarah Ahmed",
                "phone": "+923002222222",
                "email": "sarah@example.com",
            },
            {
                "name": "Usman Raza",
                "phone": "+923003333333",
                "email": "usman@example.com",
            },
            {
                "name": "Fatima Noor",
                "phone": "+923004444444",
                "email": "fatima@example.com",
            },
            {
                "name": "Hamza Malik",
                "phone": "+923005555555",
                "email": "hamza@example.com",
            },
        ]

        customers = {}

        for data in customer_data:
            result = await db.execute(
                select(Customer).where(
                    Customer.tenant_id == DEV_TENANT_ID,
                    Customer.phone == data["phone"],
                )
            )

            customer = result.scalar_one_or_none()

            if customer is None:
                customer = Customer(
                    tenant_id=DEV_TENANT_ID,
                    name=data["name"],
                    phone=data["phone"],
                    email=data["email"],
                )

                db.add(customer)
                await db.flush()

                print(f"Created customer: {customer.name}")
            else:
                print(f"Customer already exists: {customer.name}")

            customers[data["name"]] = customer

        # ---------------------------------------------------------
        # 3. LEADS
        # ---------------------------------------------------------
        lead_data = [
            {
                "customer": "Ali Khan",
                "service_interest": "Business Website",
                "urgency": "high",
                "budget": "$2000",
                "timeline": "this month",
                "lead_score": 100,
                "status": "qualified",
            },
            {
                "customer": "Sarah Ahmed",
                "service_interest": "AI Receptionist",
                "urgency": "high",
                "budget": "$3000",
                "timeline": "this week",
                "lead_score": 100,
                "status": "qualified",
            },
            {
                "customer": "Usman Raza",
                "service_interest": "Website Redesign",
                "urgency": "medium",
                "budget": "$1200",
                "timeline": "next month",
                "lead_score": 60,
                "status": "contacted",
            },
            {
                "customer": "Fatima Noor",
                "service_interest": "SEO",
                "urgency": "low",
                "budget": "$500",
                "timeline": "later",
                "lead_score": 55,
                "status": "contacted",
            },
            {
                "customer": "Hamza Malik",
                "service_interest": "AI Automation",
                "urgency": "urgent",
                "budget": "$5000",
                "timeline": "ASAP",
                "lead_score": 100,
                "status": "qualified",
            },
        ]

        leads = {}

        for data in lead_data:
            customer = customers[data["customer"]]

            result = await db.execute(
                select(Lead).where(
                    Lead.tenant_id == DEV_TENANT_ID,
                    Lead.customer_id == customer.id,
                )
            )

            lead = result.scalar_one_or_none()

            if lead is None:
                now = utc_now()

                lead = Lead(
                    tenant_id=DEV_TENANT_ID,
                    customer_id=customer.id,
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email,
                    service_interest=data["service_interest"],
                    urgency=data["urgency"],
                    budget=data["budget"],
                    timeline=data["timeline"],
                    lead_score=data["lead_score"],
                    status=data["status"],
                    created_at=now,
                    updated_at=now,

                    # Make the first follow-up immediately due.
                    next_follow_up_at=now - timedelta(minutes=5),
                    last_contacted_at=None,
                    follow_up_count=0,
                    follow_up_status="scheduled",
                )

                db.add(lead)
                await db.flush()

                print(
                    f"Created lead: {lead.name} "
                    f"(score={lead.lead_score})"
                )
            else:
                print(f"Lead already exists: {lead.name}")

            leads[data["customer"]] = lead

        # ---------------------------------------------------------
        # 4. APPOINTMENTS
        # ---------------------------------------------------------
        appointment_data = [
            {
                "customer": "Ali Khan",
                "status": "completed",
                "start_offset_days": -3,
                "start_hour": 10,
                "start_minute": 0,
            },
            {
                "customer": "Sarah Ahmed",
                "status": "completed",
                "start_offset_days": -2,
                "start_hour": 14,
                "start_minute": 0,
            },
            {
                "customer": "Usman Raza",
                "status": "scheduled",
                "start_offset_days": 2,
                "start_hour": 11,
                "start_minute": 0,
            },
            {
                "customer": "Fatima Noor",
                "status": "completed",
                "start_offset_days": -1,
                "start_hour": 15,
                "start_minute": 0,
            },
            {
                "customer": "Hamza Malik",
                "status": "completed",
                "start_offset_days": -4,
                "start_hour": 16,
                "start_minute": 0,
            },
        ]

        appointments = {}

        for data in appointment_data:
            customer = customers[data["customer"]]

            result = await db.execute(
                select(Appointment).where(
                    Appointment.tenant_id == DEV_TENANT_ID,
                    Appointment.customer_id == customer.id,
                )
            )

            appointment = result.scalar_one_or_none()

            if appointment is None:
                now = utc_now()

                # Create realistic appointment times.
                start_time = (
                    now
                    + timedelta(
                        days=data["start_offset_days"],
                    )
                ).replace(
                    hour=data["start_hour"],
                    minute=data["start_minute"],
                    second=0,
                    microsecond=0,
                )

                end_time = start_time + timedelta(minutes=30)

                appointment = Appointment(
                    tenant_id=DEV_TENANT_ID,
                    customer_id=customer.id,
                    conversation_id=None,

                    # Dummy Cal.com values.
                    # These are intentionally fake and are only for
                    # development/testing.
                    cal_booking_id=f"dummy-booking-{customer.id}",
                    cal_event_type_id=2321820,

                    status=data["status"],

                    start_time=start_time,
                    end_time=end_time,
                    time_zone="Asia/Karachi",

                    customer_name=customer.name,
                    customer_email=customer.email,
                    customer_phone=customer.phone,

                    created_at=now,
                    updated_at=now,
                )

                db.add(appointment)
                await db.flush()

                print(
                    f"Created appointment: "
                    f"{customer.name} | "
                    f"{appointment.status} | "
                    f"{appointment.start_time}"
                )

            else:
                print(
                    f"Appointment already exists: "
                    f"{customer.name}"
                )

            appointments[data["customer"]] = appointment
        # ---------------------------------------------------------
        # 5. REVIEWS
        # ---------------------------------------------------------
        review_data = [
            {
                "customer": "Ali Khan",
                "rating": 5,
                "feedback": "Excellent service and very professional.",
                "status": "completed",
            },
            {
                "customer": "Sarah Ahmed",
                "rating": 2,
                "feedback": "The experience did not meet my expectations.",
                "status": "escalated",
            },
            {
                "customer": "Fatima Noor",
                "rating": 4,
                "feedback": "Good experience overall.",
                "status": "completed",
            },
            {
                "customer": "Hamza Malik",
                "rating": None,
                "feedback": None,
                "status": "pending",
            },
        ]

        for data in review_data:
            customer = customers[data["customer"]]
            appointment = appointments[data["customer"]]

            # Review only belongs to completed appointments.
            if appointment.status != "completed":
                continue

            result = await db.execute(
                select(Review).where(
                    Review.tenant_id == DEV_TENANT_ID,
                    Review.appointment_id == appointment.id,
                )
            )

            review = result.scalar_one_or_none()

            if review is None:
                now = utc_now()

                review = Review(
                    tenant_id=DEV_TENANT_ID,
                    customer_id=customer.id,
                    appointment_id=appointment.id,
                    rating=data["rating"],
                    feedback=data["feedback"],
                    status=data["status"],

                    # Pending review is immediately due.
                    review_request_at=(
                        now - timedelta(minutes=5)
                        if data["status"] == "pending"
                        else None
                    ),

                    review_request_sent_at=None,
                    responded_at=(
                        now
                        if data["rating"] is not None
                        else None
                    ),
                    created_at=now,
                    updated_at=now,
                )

                db.add(review)
                await db.flush()

                print(
                    f"Created review: {customer.name} "
                    f"(rating={data['rating']})"
                )
            else:
                print(f"Review already exists: {customer.name}")

        # ---------------------------------------------------------
        # COMMIT
        # ---------------------------------------------------------
        await db.commit()



async def main():
    try:
        await seed()
    except Exception as exc:
        print(f"\nSEED ERROR: {exc}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())