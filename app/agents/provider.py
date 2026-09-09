from openai import AsyncOpenAI

from agents import (
    OpenAIChatCompletionsModel,
    set_default_openai_client,
)

from app.config import get_settings


settings = get_settings()


groq_client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


groq_model = OpenAIChatCompletionsModel(
    model=settings.default_model,
    openai_client=groq_client,
)


set_default_openai_client(
    groq_client,
    use_for_tracing=False,
)