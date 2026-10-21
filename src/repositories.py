from sqlalchemy import select

from src.models import Auth


class UserRepository():
    def __init__(self, session):
        self.session = session

    def get_by_proxy_user_id(self, user_id: str):
        stmt = select(Auth).where(Auth.proxy_user_id == user_id)
        result = self.session.execute(stmt)
    
        return result.scalar_one_or_none()