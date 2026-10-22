from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import UserRepository
from src.schemas import AuthRequest, AuthResponse, Context, ErrorResponse
from src.services import AuthService

# Error message -> (HTTP status code, internal error code)
ERROR_CODES = {
    "invalid username format": (400, 1000),
    "invalid password": (401, 1001),
    "no available bandwidth": (403, 1002),
    "user not found": (401, 1003),
}

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "",
    response_model=AuthResponse,
    response_model_exclude_none=True,
)
def authenticate(
    request: AuthRequest, db: Annotated[Session, Depends(get_db)]
) -> AuthResponse | JSONResponse:
    user_db = UserRepository(session=db)
    service = AuthService(user_db=user_db)
    try:
        auth_context = service.authenticate(request.username, request.password)
    except ValueError as e:
        error_msg = str(e)
        error_codes = ERROR_CODES.get(error_msg)
        if not error_codes:
            raise
        error_response = ErrorResponse(
            internal_error_code=error_codes[1], error_message=error_msg
        )

        return JSONResponse(
            status_code=error_codes[0],
            content=error_response.model_dump(),
        )

    context = Context(auth_service=auth_context)
    auth_response = AuthResponse(
        context=context,
        available_bandwidth=auth_context.available_bandwidth,
    )

    return auth_response
