from pydantic import BaseModel


class AuthRequest(BaseModel):
    username: str
    password: str


class ResidentialParams(BaseModel):
    country: str
    city: str | None = None


class AuthContext(BaseModel):
    proxy_user_id: str
    available_bandwidth: int
    residential_params: ResidentialParams | None = None


class ErrorResponse(BaseModel):
    internal_error_code: int
    error_message: str


class ProxyAddress(BaseModel):
    ip: str
    port: int


class RouteContext(BaseModel):
    proxy_addr: ProxyAddress
    protocol: str


class Context(BaseModel):
    auth_service: AuthContext
    route_service: RouteContext | None = None


class RouteRequest(BaseModel):
    context: Context
    protocol: str


class AuthResponse(BaseModel):
    context: Context
    available_bandwidth: int


class RouteResponse(BaseModel):
    context: Context
    proxy_addr: ProxyAddress
