from decimal import Decimal
from ipaddress import IPv4Address

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


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
        Numeric, nullable=False
    )


class Proxy(Base):
    __tablename__ = "residential_proxy"

    residential_proxy_id: Mapped[int] = mapped_column(primary_key=True)
    residential_proxy_ip_address_v4: Mapped[IPv4Address] = mapped_column(
        INET,
        nullable=False,
    )
    residential_proxy_port: Mapped[int] = mapped_column(nullable=False)
    country_id: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    city_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    residential_proxy_supported_protocol: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("residential_proxy_supported_protocol IN ('http', 'socks5')"),
        nullable=False,
    )
