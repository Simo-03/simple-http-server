import logging
from unittest.mock import call

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "suffix, params",
    [
        ("", None),
        ("_c_gb", {"country": "gb"}),
        ("_c_us_city_new_york", {"country": "us", "city": "new_york"}),
    ],
)
def test_auth_response_matches_spec(client, suffix, params):
    response = client.post(
        "/auth",
        json={"username": "alice_residential" + suffix, "password": "secretpass123"},
    )
    auth = {"proxy_user_id": "alice_residential", "available_bandwidth": 10737418240}
    if params is not None:
        auth["residential_params"] = params
    assert response.status_code == 200
    assert response.json() == {
        "context": {"auth_service": auth},
        "available_bandwidth": 10737418240,
    }


@pytest.mark.parametrize(
    "username, password, failure, status, code, message",
    [
        (
            "alice_residential_city_new_york",
            "secretpass123",
            None,
            400,
            1000,
            "invalid username format",
        ),
        ("alice_residential", "wrong", None, 401, 1001, "invalid password"),
        (
            "alice_residential",
            "secretpass123",
            "bandwidth",
            403,
            1002,
            "no available bandwidth",
        ),
        ("unknown_user", "secretpass123", "missing", 401, 1003, "user not found"),
    ],
)
def test_auth_errors(
    client, user, user_repository, username, password, failure, status, code, message
):
    if failure == "bandwidth":
        user.proxy_user_available_bandwidth = 0
    elif failure == "missing":
        user_repository.get_user.return_value = None

    response = client.post("/auth", json={"username": username, "password": password})

    assert response.status_code == status
    assert response.json() == {"internal_error_code": code, "error_message": message}


@pytest.mark.parametrize(
    "suffix, protocol, fallback, expected_calls",
    [
        ("_c_us_city_new_york", "http", False, [call("http", "us", "new_york")]),
        (
            "_c_us_city_missing",
            "socks5",
            True,
            [call("socks5", "us", "missing"), call("socks5", "us", None)],
        ),
        ("_c_us", "http", False, [call("http", "us", None)]),
        ("", "http", False, [call("http", None, None)]),
        ("", "socks5", False, [call("socks5", None, None)]),
    ],
)
def test_auth_to_route_preserves_context(
    client, proxy, proxy_repository, suffix, protocol, fallback, expected_calls
):
    if fallback:
        proxy_repository.get_proxy.side_effect = [None, proxy]
    auth_response = client.post(
        "/auth",
        json={"username": "alice_residential" + suffix, "password": "secretpass123"},
    )
    assert auth_response.status_code == 200
    context = auth_response.json()["context"]

    response = client.post("/route", json={"context": context, "protocol": protocol})

    address = {
        "ip": str(proxy.residential_proxy_ip_address_v4),
        "port": proxy.residential_proxy_port,
    }
    assert response.status_code == 200
    assert response.json() == {
        "context": {
            "auth_service": context["auth_service"],
            "route_service": {"proxy_addr": address, "protocol": protocol},
        },
        "proxy_addr": address,
    }
    assert proxy_repository.get_proxy.call_args_list == expected_calls


@pytest.mark.parametrize(
    "protocol, params, status, code, message",
    [
        ("ftp", None, 400, 3001, "unsupported protocol"),
        ("http", {"country": "xx"}, 404, 3400, "no proxy found for country"),
        (
            "socks5",
            {"country": "us", "city": "missing"},
            404,
            3400,
            "no proxy found for country",
        ),
        ("http", None, 404, 3400, "no proxy found for country"),
    ],
)
def test_route_errors(
    client, proxy_repository, protocol, params, status, code, message
):
    proxy_repository.get_proxy.return_value = None
    auth = {"proxy_user_id": "alice_residential", "available_bandwidth": 10737418240}
    if params is not None:
        auth["residential_params"] = params

    response = client.post(
        "/route", json={"context": {"auth_service": auth}, "protocol": protocol}
    )

    assert response.status_code == status
    assert response.json() == {"internal_error_code": code, "error_message": message}
    if protocol == "ftp":
        proxy_repository.get_proxy.assert_not_called()


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/auth", {}),
        ("/auth", {"username": "alice_residential"}),
        ("/auth", {"username": 123, "password": "secretpass123"}),
        ("/route", {}),
        (
            "/route",
            {
                "context": {
                    "auth_service": {
                        "proxy_user_id": "alice_residential",
                        "available_bandwidth": 1,
                    }
                }
            },
        ),
        ("/route", {"context": {}, "protocol": "http"}),
        ("/route", {"context": {"auth_service": None}, "protocol": "http"}),
    ],
)
def test_invalid_request_body(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 400
    assert response.json() == {
        "internal_error_code": 4000,
        "error_message": "invalid request body",
    }


@pytest.mark.parametrize("path", ["/auth", "/route"])
def test_malformed_json(client, path):
    response = client.post(
        path, content="{", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json() == {
        "internal_error_code": 4000,
        "error_message": "invalid request body",
    }


@pytest.mark.parametrize("path", ["/auth", "/route"])
def test_unknown_value_error_is_not_reported_as_business_failure(
    client, user_repository, proxy_repository, path
):
    if path == "/auth":
        user_repository.get_user.side_effect = ValueError("unexpected failure")
        payload = {"username": "alice_residential", "password": "secretpass123"}
    else:
        proxy_repository.get_proxy.side_effect = ValueError("unexpected failure")
        payload = {
            "context": {
                "auth_service": {
                    "proxy_user_id": "alice_residential",
                    "available_bandwidth": 1,
                }
            },
            "protocol": "http",
        }
    with pytest.raises(ValueError, match="^unexpected failure$"):
        client.post(path, json=payload)


@pytest.mark.parametrize(
    "path, status, message",
    [
        ("/missing", 404, "Not Found"),
        ("/auth", 405, "Method Not Allowed"),
        ("/route", 405, "Method Not Allowed"),
    ],
)
def test_framework_errors_use_common_envelope(
    client, user_repository, proxy_repository, path, status, message
):
    response = client.get(path)

    assert response.status_code == status
    assert response.json() == {
        "internal_error_code": 4001,
        "error_message": message,
    }
    if status == 405:
        assert response.headers["allow"] == "POST"
    user_repository.get_user.assert_not_called()
    proxy_repository.get_proxy.assert_not_called()


@pytest.mark.parametrize("path", ["/auth", "/route"])
@pytest.mark.parametrize("exception_type", [ValueError, RuntimeError])
def test_unexpected_failures_return_generic_json_and_log_traceback(
    client, user_repository, proxy_repository, caplog, path, exception_type
):
    failure = exception_type("private database information")
    if path == "/auth":
        user_repository.get_user.side_effect = failure
        payload = {"username": "alice_residential", "password": "secretpass123"}
    else:
        proxy_repository.get_proxy.side_effect = failure
        payload = {
            "context": {
                "auth_service": {
                    "proxy_user_id": "alice_residential",
                    "available_bandwidth": 1,
                }
            },
            "protocol": "http",
        }

    # Starlette still re-raises unexpected errors for server logging. Disable
    # TestClient's re-raising here to inspect the response sent to a real client.
    with (
        caplog.at_level(logging.ERROR, logger="src.main"),
        TestClient(client.app, raise_server_exceptions=False) as response_client,
    ):
        response = response_client.post(path, json=payload)

    assert response.status_code == 500
    assert response.json() == {
        "internal_error_code": 5000,
        "error_message": "internal server error",
    }
    assert any(
        record.name == "src.main"
        and record.levelno == logging.ERROR
        and f"POST {path}" in record.getMessage()
        and record.exc_info is not None
        and record.exc_info[1] is failure
        and record.exc_info[2] is not None
        for record in caplog.records
    )
