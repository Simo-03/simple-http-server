import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.auth import router as auth_router
from src.route import router as proxy_router
from src.schemas import ErrorResponse

app = FastAPI()

logger = logging.getLogger(__name__)

app.include_router(auth_router)
app.include_router(proxy_router)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    error_response = ErrorResponse(
        internal_error_code=4000, error_message="invalid request body"
    )

    return JSONResponse(status_code=400, content=error_response.model_dump())


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(
    request: Request,
    exc: StarletteHTTPException,
):
    error_response = ErrorResponse(
        internal_error_code=4001,
        error_message=str(exc.detail),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(
    request: Request,
    exc: Exception,
):
    logger.error(
        "Unexpected error handling %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    error_response = ErrorResponse(
        internal_error_code=5000,
        error_message="internal server error",
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


@app.get("/")
def root():
    return {"status": "ok"}
