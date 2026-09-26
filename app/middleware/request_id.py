import logging
import time
import uuid

from fastapi import Request
from app.core.request_context import request_id_context

logger = logging.getLogger(__name__)


async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())
    token = request_id_context.set(request_id)
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        logger.exception(
            "%s %s failed",
            request.method,
            request.url.path,
        )
        raise

    finally:
        request_id_context.reset(token)