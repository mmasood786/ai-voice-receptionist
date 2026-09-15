from agents import Agent, Runner

from app.agents.provider import groq_model


class LeadEmailGenerator:

    def __init__(self):
        self.agent = Agent(
            name="Lead Follow-Up Writer",
            model=groq_model,
            instructions="""
                            You write short, professional follow-up emails for business leads.

                            Rules:
                            - Be natural and helpful.
                            - Never invent information.
                            - Use only the lead information provided.
                            - Do not mention internal lead scores, IDs, databases, or automation.
                            - Do not pressure the customer.
                            - Keep the email under 120 words.
                            - Do not use emojis.
                            - Do not use exaggerated marketing claims.
                            - Include a simple invitation to reply.
                            - Return ONLY the email body.
                            """,
        )

    async def generate(
        self,
        *,
        customer_name: str,
        service_interest: str | None,
        urgency: str | None,
        budget: str | None,
        timeline: str | None,
        follow_up_count: int,
    ) -> str:

        prompt = f"""
                    Write a follow-up email for this lead.

                    Customer name:
                    {customer_name}

                    Service interest:
                    {service_interest or "Not provided"}

                    Urgency:
                    {urgency or "Not provided"}

                    Budget:
                    {budget or "Not provided"}

                    Timeline:
                    {timeline or "Not provided"}

                    This is follow-up number:
                    {follow_up_count + 1}
                    """

        result = await Runner.run(
            self.agent,
            prompt,
        )

        return result.final_output.strip()
