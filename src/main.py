from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


from src.auth import router as auth_router
from src.schemas import ErrorResponse


app = FastAPI()

app.include_router(auth_router)

@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    error_response = ErrorResponse(
        internal_error_code=4000,
        error_message="invalid request body"
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump()
    )

@app.get("/")
def root():
    return {"status": "ok"}

