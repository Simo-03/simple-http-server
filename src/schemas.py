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


#TODO: write the route_sevice class and proxy_addr
#TODO: update the context class to accomodate routing

class Context(BaseModel):
    auth_service: AuthContext
    # route_service: RouteContext | None = None


class AuthResponse(BaseModel):
    context: Context
    available_bandwidth: int