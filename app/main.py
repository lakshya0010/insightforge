import time
import logging
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request
from app.api.v1.router import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)


setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


app.include_router(router, prefix="/api/v1")
@app.middleware("http")
async def log_requests(request:Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time()-start_time
    print(
        f"{request.method} {request.url.path}\n"
        f"completed in {process_time:.4f}s\n"
        f"status={response.status_code}\n"
    )
    return response

logger.info(f"{settings.APP_NAME} started")
