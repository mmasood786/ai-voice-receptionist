from datetime import datetime, timezone
from agents import function_tool, RunContextWrapper

from app.db.database import AsyncSessionLocal
from app.services.customer_service import CustomerService
from app.services.lead_service import LeadService
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService
from app.services.knowledge_search_service import KnowledgeSearchService

from app.config import get_settings
from app.agents.context import AgentContext
from zoneinfo import ZoneInfo
from app.agents.escalation import escalate_to_human
from app.services.conversation_service import ConversationService

# Temporary development tenant.
# Later this will come from authentication/runtime context.
DEV_TENANT_ID = 1

@function_tool
async def find_customer(
    ctx: RunContextWrapper[AgentContext],
    phone: str,
    email: str | None,
) -> dict:
    """
    Find a customer using phone and optional email.

    Email must be provided when known.
    Use null when the customer did not provide an email.
    """

    tenant_id = ctx.context.tenant_id

    async with AsyncSessionLocal() as db:

        service = CustomerService(db)

        result = await service.resolve_customer(
            tenant_id=tenant_id,
            phone=phone,
            email=email,
        )

        status = result["status"]

        # ----------------------------------
        # EXACT MATCH
        # ----------------------------------

        if status == "exact_match":
            customer = result["customer"]

            ctx.context.customer_id = customer.id

            conversation_service = ConversationService(db)

            await conversation_service.set_customer(
                tenant_id=tenant_id,
                conversation_id=ctx.context.conversation_id,
                customer_id=customer.id,
            )

            await db.commit()

            return {
                "success": True,
                "status": "exact_match",
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "phone": customer.phone,
                    "email": customer.email,
                },
            }

        # ----------------------------------
        # POSSIBLE CONFLICT
        # ----------------------------------

        if status == "possible_conflict":

            matches = result["matches"]

            return {
                "success": True,
                "status": "possible_conflict",
                "message": (
                    "This phone number is already associated "
                    "with another customer."
                ),
                "matches": [
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "phone": customer.phone,
                        "email": customer.email,
                    }
                    for customer in matches
                ],
            }

        # ----------------------------------
        # NEW CUSTOMER
        # ----------------------------------

        return {
            "success": True,
            "status": "new_customer",
            "customer": None,
        }

@function_tool
async def create_customer(
    ctx: RunContextWrapper[AgentContext],
    name: str,
    phone: str,
    email: str | None,
) -> dict:
    """
    Create a new customer.

    Email must be provided when known.
    Use null when the customer did not provide an email.
    """

    tenant_id = ctx.context.tenant_id

    async with AsyncSessionLocal() as db:

        service = CustomerService(db)

        customer = await service.create_customer(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
        )

        ctx.context.customer_id = customer.id

        conversation_service = ConversationService(db)

        await conversation_service.set_customer(
            tenant_id=tenant_id,
            conversation_id=ctx.context.conversation_id,
            customer_id=customer.id,
        )

        await db.commit()

        return {
            "success": True,
            "status": "created",
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
            },
        }
  
@function_tool
async def get_lead(
    ctx: RunContextWrapper[AgentContext],
) -> dict:
    """
    Retrieve the lead associated with the current conversation.
    """

    tenant_id = ctx.context.tenant_id
    lead_id = ctx.context.lead_id

    # -----------------------------------------
    # Validate context
    # -----------------------------------------
    if lead_id is None:
        return {
            "success": False,
            "error": "lead_context_missing",
            "message": "No lead is associated with this conversation.",
        }

    async with AsyncSessionLocal() as db:
        service = LeadService(db)

        lead = await service.get_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

        if not lead:
            return {
                "success": True,
                "found": False,
                "lead": None,
            }

        return {
            "success": True,
            "found": True,
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "status": lead.status,
                "lead_score": lead.lead_score,
                "service_interest": lead.service_interest,
                "urgency": lead.urgency,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "notes": lead.notes,
            },
        }

@function_tool
async def update_lead(
    ctx: RunContextWrapper[AgentContext],
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Update the lead associated with the current conversation.
    """

    tenant_id = ctx.context.tenant_id
    lead_id = ctx.context.lead_id

    # -----------------------------------------
    # Validate context
    # -----------------------------------------
    if lead_id is None:
        return {
            "success": False,
            "error": "lead_context_missing",
            "message": "No lead is associated with this conversation.",
        }

    async with AsyncSessionLocal() as db:
        service = LeadService(db)

        lead = await service.update_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
            name=name,
            phone=phone,
            email=email,
            status=status,
            notes=notes,
        )

        if not lead:
            return {
                "success": False,
                "error": "lead_not_found",
                "message": "The lead could not be found.",
            }

        await db.commit()

        return {
            "success": True,
            "message": "Lead updated successfully.",
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "status": lead.status,
                "lead_score": lead.lead_score,
                "notes": lead.notes,
            },
        }
        
@function_tool
async def check_availability(
    ctx: RunContextWrapper[AgentContext],
    start_time: str,
    end_time: str,
    time_zone: str = "Asia/Karachi",
) -> dict:
    """
    Check real appointment availability in Cal.com.

    start/end must be ISO-8601 timezone-aware datetimes.
    """

    try:
        # Validate timezone
        ZoneInfo(time_zone)

        # Parse datetime
        start_dt = datetime.fromisoformat(
            start_time.replace("Z", "+00:00")
        )

        end_dt = datetime.fromisoformat(
            end_time.replace("Z", "+00:00")
        )

        if start_dt.tzinfo is None:
            raise ValueError(
                "start must include timezone information"
            )

        if end_dt.tzinfo is None:
            raise ValueError(
                "end must include timezone information"
            )

        if end_dt <= start_dt:
            raise ValueError(
                "end must be after start"
            )

        # Prevent stale dates
        now = datetime.now(timezone.utc)

        if start_dt < now:
            return {
                "success": False,
                "error": "past_datetime",
                "message": (
                    "The requested availability window is in the past. "
                    "Please provide a future date."
                ),
                "slots": [],
                "count": 0,
            }

        service = AvailabilityService()

        slots = await service.get_available_slots(
            start_time=start_dt,
            end_time=end_dt,
            time_zone=time_zone,
        )

        return {
            "success": True,
            "timezone": time_zone,
            "slots": slots,
            "count": len(slots),
        }

    except Exception as exc:
        print("\n❌ CHECK AVAILABILITY FAILED")
        print("Exception type:", type(exc).__name__)
        print("Exception:", repr(exc))

        return {
            "success": False,
            "error": str(exc),
            "slots": [],
            "count": 0,
        }
            
@function_tool
async def create_booking(
    ctx: RunContextWrapper[AgentContext],
    start_time: str,
    end_time: str,
    customer_name: str,
    customer_email: str | None,
    customer_phone: str | None,
    time_zone: str = "Asia/Karachi",
) -> dict:
    """
    Create a confirmed appointment in Cal.com and save it
    to PostgreSQL.
    """

    try:
        start_dt = datetime.fromisoformat(
            start_time.replace("Z", "+00:00")
        )

        end_dt = datetime.fromisoformat(
            end_time.replace("Z", "+00:00")
        )

        if start_dt.tzinfo is None:
            raise ValueError(
                "start must include timezone information"
            )

        if end_dt.tzinfo is None:
            raise ValueError(
                "end must include timezone information"
            )

        if end_dt <= start_dt:
            raise ValueError(
                "end must be after start"
            )

        settings = get_settings()

        tenant_id = ctx.context.tenant_id
        conversation_id = ctx.context.conversation_id
        customer_id = ctx.context.customer_id

        # A booking should normally be associated with
        # a customer.
        if customer_id is None:
            return {
                "success": False,
                "error": "customer_context_missing",
                "message": (
                    "A customer must be identified before booking."
                ),
            }

        async with AsyncSessionLocal() as db:

            service = BookingService(db)

            result = await service.create_booking(
                tenant_id=tenant_id,
                customer_id=customer_id,
                conversation_id=conversation_id,

                start_time=start_dt,
                end_time=end_dt,

                time_zone=time_zone,

                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,

                cal_event_type_id=int(settings.cal_event_type_id),
            )
            
            
            # Handle booking conflict or other service-level failure
            if result.get("success") is False:
                return result

            await db.commit()

            appointment = result["appointment"]

            return {
                "success": True,
                "appointment_id": appointment.id,
                "cal_booking_id": appointment.cal_booking_id,
                "customer_id": appointment.customer_id,
                "conversation_id": appointment.conversation_id,
                "status": appointment.status,
                "start": appointment.start_time.isoformat(),
                "end": appointment.end_time.isoformat(),
                "time_zone": appointment.time_zone,
                "message": (
                    "Appointment successfully booked."
                ),
            }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
            "message": (
                "The appointment could not be booked."
            ),
        }
        
@function_tool
async def create_lead(
    ctx: RunContextWrapper[AgentContext],
    name: str,
    phone: str,
    email: str | None,
    notes: str | None,
) -> dict:
    """
    Create a CRM lead.

    Always provide email and notes.
    Use null when not available.
    """

    tenant_id = ctx.context.tenant_id
    customer_id = ctx.context.customer_id
    conversation_id = ctx.context.conversation_id

    if customer_id is None:
        return {
            "success": False,
            "error": "customer_context_missing",
            "message": (
                "A customer must be identified "
                "before creating a lead."
            ),
        }

    async with AsyncSessionLocal() as db:

        service = LeadService(db)

        lead = await service.create_lead(
            tenant_id=tenant_id,
            customer_id=customer_id,
            name=name,
            phone=phone,
            email=email,
            notes=notes,
        )

        # Persist lead ID on the conversation
        conversation_service = ConversationService(db)

        await conversation_service.set_lead(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            lead_id=lead.id,
        )

        await db.commit()

        ctx.context.lead_id = lead.id

        return {
            "success": True,
            "lead": {
                "id": lead.id,
                "customer_id": lead.customer_id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "status": lead.status,
                "lead_score": lead.lead_score,
            },
        }
        
@function_tool
async def qualify_lead(
    ctx: RunContextWrapper[AgentContext],
    service_interest: str | None,
    urgency: str | None,
    budget: str | None,
    timeline: str | None,
) -> dict:
    """
    Save qualification information for the current lead.
    """

    tenant_id = ctx.context.tenant_id
    conversation_id = ctx.context.conversation_id
    lead_id = ctx.context.lead_id

    # -----------------------------------------
    # Load lead context if missing
    # -----------------------------------------
    try:
        async with AsyncSessionLocal() as db:

            # If this AgentContext does not have lead_id,
            # restore it from the conversation.
            if lead_id is None:
                conversation_service = ConversationService(db)

                conversation = await conversation_service.get_by_id(
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                )

                if conversation is not None:
                    lead_id = conversation.lead_id
                    ctx.context.lead_id = lead_id

            # -----------------------------------------
            # Validate context
            # -----------------------------------------
            if lead_id is None:
                return {
                    "success": False,
                    "error": "lead_context_missing",
                    "message": (
                        "No lead is associated with this conversation."
                    ),
                }

            service = LeadService(db)

            # -----------------------------------------
            # Qualify lead
            # -----------------------------------------
            lead = await service.qualify_lead(
                tenant_id=tenant_id,
                lead_id=lead_id,
                service_interest=service_interest,
                urgency=urgency,
                budget=budget,
                timeline=timeline,
            )

            # -----------------------------------------
            # Lead not found
            # -----------------------------------------
            if lead is None:
                return {
                    "success": False,
                    "error": "lead_not_found",
                    "message": "The lead could not be found.",
                }

            # -----------------------------------------
            # Commit transaction
            # -----------------------------------------
            await db.commit()

            print("✅ DATABASE COMMIT COMPLETED")

            # -----------------------------------------
            # Success response
            # -----------------------------------------
            return {
                "success": True,
                "message": "Lead qualification updated successfully.",
                "lead": {
                    "id": lead.id,
                    "customer_id": lead.customer_id,
                    "name": lead.name,
                    "service_interest": lead.service_interest,
                    "urgency": lead.urgency,
                    "budget": lead.budget,
                    "timeline": lead.timeline,
                    "lead_score": lead.lead_score,
                    "status": lead.status,
                },
            }

    # -----------------------------------------
    # Database / SQLAlchemy errors
    # -----------------------------------------
    except Exception as exc:
        print("\n❌ QUALIFY LEAD FAILED")
        print("Exception type:", type(exc).__name__)
        print("Exception:", repr(exc))

        return {
            "success": False,
            "error": "qualification_failed",
            "message": (
                "I could not update the lead qualification. "
                "Please try again or offer human assistance."
            ),
        }
           
@function_tool
async def search_knowledge(
    ctx: RunContextWrapper[AgentContext],
    query: str,
) -> str:
    """
        MANDATORY TOOL FOR BUSINESS INFORMATION.

        Use this tool whenever the customer asks about:
        - services
        - pricing
        - packages
        - website costs
        - timelines
        - process
        - FAQs
        - policies
        - what the business offers

        Do not answer these questions from memory.
        Search this tool first.
    """
    
    print("\n" + "=" * 60)
    print("SEARCH_KNOWLEDGE CALLED")
    print("QUERY:", query)
    print("TENANT ID:", ctx.context.tenant_id)
    print("=" * 60)

    try:
        print("STEP 1: Opening database session...")

        async with AsyncSessionLocal() as db:

            print("STEP 1 OK: Database session opened")

            print("STEP 2: Creating KnowledgeSearchService...")

            service = KnowledgeSearchService(db)

            print("STEP 2 OK: Service created")

            print("STEP 3: Searching knowledge...")

            results = await service.search(
                tenant_id=ctx.context.tenant_id,
                query=query,
                limit=4,
            )

            print("STEP 3 OK: Knowledge search completed")
            print("RESULT COUNT:", len(results))

        if not results:
            print("NO RESULTS FOUND")
            return "No relevant business information was found."

        print("STEP 4: Formatting results...")

        sections = []

        for result in results:
            sections.append(
                f"Knowledge:\n{result['content']}"
            )

        response = "\n\n".join(sections)

        print("STEP 4 OK")
        print("KNOWLEDGE RESULT:")
        print(response)
        print("=" * 60)

        return response

    except Exception as e:

        print("\n" + "!" * 60)
        print("SEARCH_KNOWLEDGE ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("!" * 60)

        import traceback
        traceback.print_exc()

        return (
            "I was unable to retrieve the business information right now. "
            "Please offer human assistance."
        )
        
@function_tool
async def cancel_booking(
    ctx: RunContextWrapper[AgentContext],
    cancellation_reason: str | None = None,
) -> dict:
    """
    Cancel the customer's existing appointment.

    Use this tool when the customer explicitly asks to cancel
    an appointment.

    The appointment is identified internally using the current
    customer and conversation context. Never ask the customer
    for internal appointment IDs or Cal.com booking IDs.
    """

    context = ctx.context

    if not context.customer_id:
        return {
            "success": False,
            "error": "customer_context_missing",
            "message": "I need to identify the customer before cancelling an appointment.",
        }
    
    async with AsyncSessionLocal() as db:

        service = BookingService(db)

        result = await service.cancel_booking(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            conversation_id=context.conversation_id,
            cancellation_reason=cancellation_reason,
            time_zone=context.time_zone,
        )

        return result    
        
@function_tool
async def reschedule_booking(
    ctx: RunContextWrapper[AgentContext],
    start_time: str,
    end_time: str,
) -> dict:
    """
    Reschedule the customer's existing appointment.

    Use this when the customer explicitly wants to change
    the date or time of an existing appointment.

    Never ask the customer for appointment IDs, Cal.com
    booking IDs, booking UIDs, tenant IDs, or database IDs.
    """

    context = ctx.context

    if not context.customer_id:
        return {
            "success": False,
            "error": "customer_context_missing",
            "message": (
                "I need to identify the customer before "
                "rescheduling the appointment."
            ),
        }

    try:
        parsed_start = datetime.fromisoformat(start_time)
        parsed_end = datetime.fromisoformat(end_time)

    except ValueError:
        return {
            "success": False,
            "error": "invalid_datetime",
            "message": (
                "The requested appointment date or time "
                "could not be understood."
            ),
        }

    async with AsyncSessionLocal() as db:
        service = BookingService(db)

        return await service.reschedule_booking(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            conversation_id=context.conversation_id,
            start_time=parsed_start,
            end_time=parsed_end,
            time_zone=context.time_zone or "Asia/Karachi",
        )
        
        
        
tools = [
    find_customer,
    create_customer,
    create_lead,
    qualify_lead,
    get_lead,
    update_lead,
    escalate_to_human,
    check_availability,
    create_booking,
    search_knowledge,
    cancel_booking,
    reschedule_booking
]