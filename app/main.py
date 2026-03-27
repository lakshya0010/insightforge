import time
from fastapi import FastAPI, Request
from app.api.v1.router import router
from core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

@app.middleware("http")
async def log_requests(request:Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time()-start_time
    print(
        f"{request.method} {request.url.path}"
        f"completed in {process_time:.4f}s"
        f"status={response.status_code}"
    )
    return response

app.include_router(router, prefix="/api/v1")
