import os
from decimal import Decimal
from ipaddress import IPv4Address
from unittest.mock import Mock

# The application creates an engine on import. Never let ordinary tests use .env.
os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@127.0.0.1:1/unused"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import get_db
from src.main import app
from src.models import Proxy, User
from src.repositories import ProxyRepository, UserRepository


@pytest.fixture
def user():
    return User(
        proxy_user_id="alice_residential",
        proxy_user_password="secretpass123",
        proxy_user_available_bandwidth=Decimal(10737418240),
    )


@pytest.fixture
def proxy():
    return Proxy(
        residential_proxy_id=1,
        residential_proxy_ip_address_v4=IPv4Address("192.168.1.1"),
        residential_proxy_port=8080,
        country_id="us",
        city_id="new_york",
        residential_proxy_supported_protocol="http",
    )


@pytest.fixture
def user_repository(user):
    repository = Mock(spec=UserRepository)
    repository.get_user.return_value = user
    return repository


@pytest.fixture
def proxy_repository(proxy):
    repository = Mock(spec=ProxyRepository)
    repository.get_proxy.return_value = proxy
    return repository


@pytest.fixture
def client(monkeypatch, user_repository, proxy_repository):
    # Keep real handlers, services, validation and response serialization.
    # Replace only database access, so no live server or database is required.
    monkeypatch.setattr("src.auth.UserRepository", lambda session: user_repository)
    monkeypatch.setattr("src.route.ProxyRepository", lambda session: proxy_repository)

    def override_db():
        yield Mock(spec=Session)

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
