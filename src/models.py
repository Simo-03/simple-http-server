from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from decimal import Decimal




class User(Base):
    __tablename__ = "residential_proxy_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    proxy_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    proxy_user_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    proxy_user_available_bandwidth: Mapped[Decimal] = mapped_column(
        Numeric,
        nullable=False
    )

    