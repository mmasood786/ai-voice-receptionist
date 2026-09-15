from app.agents.provider import groq_model
from agents import Agent, Runner


class ReviewEmailGenerator:
    def __init__(self):
        self.agent = Agent(
            name="Review Request Writer",
            model=groq_model,
            instructions="""
                            You write short, friendly customer feedback request emails.

                            Rules:
                            - Be professional and natural.
                            - Thank the customer for choosing the business.
                            - Ask for honest feedback about their recent appointment.
                            - Never pressure the customer to leave a positive review.
                            - Never offer incentives for positive reviews.
                            - Never mention internal IDs, databases, automation, or AI.
                            - Keep the email under 100 words.
                            - Do not use emojis.
                            - Return ONLY the email body.
                        """,
        )

    async def generate(
        self,
        *,
        customer_name: str,
        service_name: str | None = None,
    ) -> str:

        prompt = f"""
                    Write a customer feedback request email.

                    Customer name:
                    {customer_name}

                    Service:
                    {service_name or "our service"}

                    The customer recently completed an appointment.

                    Ask them to share honest feedback about their experience.
                """

        result = await Runner.run(
            self.agent,
            prompt,
        )

        return result.final_output.strip()