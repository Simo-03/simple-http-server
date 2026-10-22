from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import ProxyRepository
from src.schemas import Context, ErrorResponse, RouteRequest, RouteResponse
from src.services import RouteService

ERROR_CODES = {
    "unsupported protocol": (400, 3001),
    "no proxy found for country": (404, 3400),
}

router = APIRouter(prefix="/route", tags=["route"])


@router.post(
    "",
    response_model=RouteResponse,
    response_model_exclude_none=True,
)
def route(
    request: RouteRequest, db: Annotated[Session, Depends(get_db)]
) -> RouteResponse | JSONResponse:
    proxy_db = ProxyRepository(session=db)
    service = RouteService(proxy_db=proxy_db)
    # This stage trusts the auth context supplied by an internal caller.
    # It selects a proxy without authenticating again or consuming bandwidth.
    params = request.context.auth_service.residential_params
    country = params.country if params is not None else None
    city = params.city if params is not None else None

    try:
        route_context = service.route(request.protocol, country, city)
    except ValueError as e:
        error_msg = str(e)
        error_codes = ERROR_CODES.get(error_msg)
        if not error_codes:
            # Let unexpected errors reach the global handler with their original traceback.
            raise
        error_response = ErrorResponse(
            internal_error_code=error_codes[1], error_message=error_msg
        )

        return JSONResponse(
            status_code=error_codes[0],
            content=error_response.model_dump(),
        )

    context = Context(
        auth_service=request.context.auth_service,
        route_service=route_context,
    )
    route_response = RouteResponse(
        context=context,
        proxy_addr=context.route_service.proxy_addr,
    )

    return route_response
