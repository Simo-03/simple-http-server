from unittest.mock import call

import pytest

from src.services import RouteService


@pytest.mark.parametrize(
    "protocol, country, city",
    [
        ("http", "us", "new_york"),
        ("socks5", "us", "chicago"),
        ("http", "us", None),
        ("http", None, None),
        ("socks5", None, None),
    ],
)
def test_route_returns_address_and_protocol(
    protocol, country, city, proxy, proxy_repository
):
    proxy.residential_proxy_supported_protocol = protocol
    result = RouteService(proxy_repository).route(protocol, country, city)

    assert result.model_dump() == {
        "proxy_addr": {"ip": "192.168.1.1", "port": 8080},
        "protocol": protocol,
    }
    proxy_repository.get_proxy.assert_called_once_with(protocol, country, city)


@pytest.mark.parametrize("protocol", ["http", "socks5"])
def test_city_miss_falls_back_to_same_country_and_protocol(
    protocol, proxy, proxy_repository
):
    proxy_repository.get_proxy.side_effect = [None, proxy]

    result = RouteService(proxy_repository).route(protocol, "us", "missing_city")

    assert result.proxy_addr.ip == "192.168.1.1"
    assert result.protocol == protocol
    assert proxy_repository.get_proxy.call_args_list == [
        call(protocol, "us", "missing_city"),
        call(protocol, "us", None),
    ]


@pytest.mark.parametrize(
    "country, city, expected_calls",
    [
        (
            "xx",
            "missing_city",
            [call("http", "xx", "missing_city"), call("http", "xx", None)],
        ),
        ("xx", None, [call("http", "xx", None)]),
        (None, None, [call("http", None, None)]),
    ],
)
def test_missing_proxy_fails_without_widening_country(
    country, city, expected_calls, proxy_repository
):
    proxy_repository.get_proxy.return_value = None

    with pytest.raises(ValueError, match="^no proxy found for country$"):
        RouteService(proxy_repository).route("http", country, city)

    assert proxy_repository.get_proxy.call_args_list == expected_calls


@pytest.mark.parametrize("protocol", ["ftp", "HTTP", "SOCKS5", ""])
def test_unsupported_protocol_does_not_query_repository(protocol, proxy_repository):
    with pytest.raises(ValueError, match="^unsupported protocol$"):
        RouteService(proxy_repository).route(protocol, "us", "new_york")
    proxy_repository.get_proxy.assert_not_called()
