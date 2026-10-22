from sqlalchemy import select

from src.models import User


class UserRepository():
    def __init__(self, session):
        self.session = session

    def get_user(self, user_id: str) -> User | None:
        stmt = select(User).where(User.proxy_user_id == user_id)
        result = self.session.execute(stmt)
    
        return result.scalar_one_or_none()