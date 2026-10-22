from sqlalchemy import select, func
from src.models import User, Proxy
from typing import Optional

class UserRepository():
    def __init__(self, session):
        self.session = session

    def get_user(self, user_id: str) -> User | None:
        stmt = select(User).where(User.proxy_user_id == user_id)
        result = self.session.execute(stmt)

        return result.scalar_one_or_none()


class ProxyRepository():
    def __init__(self, session):
        self.session = session

    def get_proxy(
        self,
        protocol: str,
        country: Optional[str] = None,
        city: Optional[str] = None) -> Proxy | None:

        stmt = select(Proxy).where(
            Proxy.residential_proxy_supported_protocol == protocol
        )
        if country is not None:
            stmt = stmt.where(Proxy.country_id == country)
        if city is not None:
            stmt = stmt.where(Proxy.city_id == city)
        stmt = stmt.order_by(func.random()).limit(1)
        result = self.session.execute(stmt)

        return result.scalar_one_or_none()
