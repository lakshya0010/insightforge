import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.response import APIResponse

logger = logging.getLogger(__name__)

async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
) -> JSONResponse:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }
    code = code_map.get(exc.status_code, "ERROR")

    logger.warning(
        f"HTTP {exc.status_code } | {request.method} {request.url.path} | {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse.fail(code=code, message=exc.detail).model_dump()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    # Extract the first validation error for a clean message.
    # Pydantic gives you all errors — we surface the first one.
    errors = exc.errors()
    first = errors[0]
    field = " → ".join(str(loc) for loc in first["loc"])
    message = f"{field}: {first['msg']}"

    logger.warning(
        f"Validation error | {request.method} {request.url.path} | {message}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIResponse.fail(
            code="VALIDATION_ERROR",
            message=message
        ).model_dump()
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    logger.error(
        f"Unhandled exception | {request.method} {request.url.path}",
        exc_info=True 
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred"
        ).model_dump()
    )