from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.webhooks import router as webhook_router
from app.api.reviews import router as reviews_router
from app.api.knowledge import router as knowledge_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from app.api.vapi_webhooks import router as vapi_webhooks_router

from app.config import get_settings

from app.api.exception_handlers import global_exception_handler
from fastapi.exceptions import RequestValidationError
from app.api.validation_handlers import validation_exception_handler
from app.core.logging_config import setup_logging
from app.middleware.request_id import request_id_middleware


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


setup_logging()
app.middleware("http")(request_id_middleware)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(health_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(webhook_router)
app.include_router(reviews_router)
app.include_router(knowledge_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(vapi_webhooks_router)

@app.get("/")
async def root():
    return {
        "application": settings.app_name,
        "status": "running",
    }