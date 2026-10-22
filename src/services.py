import re

import pycountry

from src.repositories import ProxyRepository, UserRepository
from src.schemas import AuthContext, ProxyAddress, ResidentialParams, RouteContext

SUPPORTED_PROTOCOLS = ["http", "socks5"]


class AuthService:
    def __init__(self, user_db: UserRepository) -> None:
        self.user_db = user_db

    def authenticate(self, username: str, password: str) -> AuthContext:
        user_id, country, city = parse_username(username)
        user = self.user_db.get_user(user_id)

        if user is None:
            raise ValueError("user not found")

        if password != user.proxy_user_password:
            raise ValueError("invalid password")

        if user.proxy_user_available_bandwidth == 0:
            raise ValueError("no available bandwidth")
        user_bandwidth = user.proxy_user_available_bandwidth

        if country:
            auth_context = AuthContext(
                proxy_user_id=user_id,
                available_bandwidth=user_bandwidth,
                residential_params=ResidentialParams(
                    country=country,
                    city=city,
                ),
            )
        else:
            auth_context = AuthContext(
                proxy_user_id=user_id,
                available_bandwidth=user_bandwidth,
                residential_params=None,
            )

        return auth_context


class RouteService:
    def __init__(self, proxy_db: ProxyRepository) -> None:
        self.proxy_db = proxy_db

    def route(
        self, protocol: str, country: str | None = None, city: str | None = None
    ) -> RouteContext:

        if protocol not in SUPPORTED_PROTOCOLS:
            raise ValueError("unsupported protocol")

        proxy = self.proxy_db.get_proxy(protocol, country, city)

        # country fallback
        if proxy is None and country is not None and city is not None:
            proxy = self.proxy_db.get_proxy(protocol, country, None)

        if proxy is None:
            raise ValueError("no proxy found for country")

        proxy_address = ProxyAddress(
            ip=str(proxy.residential_proxy_ip_address_v4),
            port=proxy.residential_proxy_port,
        )

        route_context = RouteContext(
            proxy_addr=proxy_address,
            protocol=protocol,
        )

        return route_context


def validate_user_id(user_id: str) -> None:
    # Letters, digits, and underscores; at least one character
    user_id_pattern = r"[A-Za-z0-9_]+"
    if re.fullmatch(user_id_pattern, user_id) is None:
        raise ValueError("invalid username format")


def validate_country(country: str) -> None:
    # Exactly two lowercase ASCII letters
    country_pattern = r"[a-z]{2}"
    # Validates ISO country-code membership
    country_details = pycountry.countries.get(alpha_2=country.upper())
    if re.fullmatch(country_pattern, country) is None or country_details is None:
        raise ValueError("invalid username format")


def validate_city(city: str) -> None:
    # Lowercase words separated by single underscores
    city_pattern = r"[a-z]+(?:_[a-z]+)*"
    if re.fullmatch(city_pattern, city) is None:
        raise ValueError("invalid username format")


def parse_username(username: str) -> tuple[str, str | None, str | None]:
    if not username:
        raise ValueError("invalid username format")

    if "_city_" in username:
        if "_c_" not in username:
            raise ValueError("invalid username format")

        else:
            user_id, _, addr = username.partition("_c_")

            if not addr:
                raise ValueError("invalid username format")

            country, _, city = addr.partition("_city_")

            validate_user_id(user_id)
            validate_country(country)
            validate_city(city)
            return (user_id, country, city)

    elif "_c_" in username:
        user_id, _, country = username.partition("_c_")

        validate_user_id(user_id)
        validate_country(country)
        return (user_id, country, None)

    else:
        user_id = username

        validate_user_id(user_id)
        return (user_id, None, None)
