

from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    app_name: str = "AI Voice Receptionist"

    app_env: str = "development"

    debug: bool = True

    database_url: str

    groq_api_key: str

    default_model: str
    
    cal_api_key: str
    cal_api_version: str = "2026-02-25"
    cal_event_type_id: int
    
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    
    resend_api_key: str
    resend_from_email: str
    resend_from_name: str = "Demo Service Company"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()