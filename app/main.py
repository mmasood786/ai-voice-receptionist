from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.config import get_settings

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(voice_router)

@app.get("/")
async def root():
    return {
        "application": settings.app_name,
        "status": "running",
    }