import pytest

from src.services import AuthService, parse_username


@pytest.mark.parametrize(
    "username, expected",
    [
        ("alice_residential", ("alice_residential", None, None)),
        ("user_123", ("user_123", None, None)),
        ("alice_residential_c_gb", ("alice_residential", "gb", None)),
        (
            "alice_residential_c_us_city_new_york",
            ("alice_residential", "us", "new_york"),
        ),
    ],
)
def test_parse_username(username, expected):
    assert parse_username(username) == expected


@pytest.mark.parametrize(
    "username",
    [
        "",
        "alice-residential",
        "alice residential",
        "alice_residential_city_new_york",
        "_c_us",
        "alice_residential_c_",
        "alice_residential_c_US",
        "alice_residential_c_usa",
        "alice_residential_c_us_city_",
        "alice_residential_c_us_city_New_York",
        "alice_residential_c_us_city_new__york",
    ],
)
def test_reject_invalid_username_before_database_lookup(username, user_repository):
    with pytest.raises(ValueError, match="^invalid username format$"):
        AuthService(user_repository).authenticate(username, "secretpass123")
    user_repository.get_user.assert_not_called()


@pytest.mark.parametrize(
    "suffix, params",
    [
        ("", None),
        ("_c_gb", {"country": "gb"}),
        ("_c_us_city_new_york", {"country": "us", "city": "new_york"}),
    ],
)
def test_authenticate_returns_parsed_context(suffix, params, user_repository):
    result = AuthService(user_repository).authenticate(
        "alice_residential" + suffix, "secretpass123"
    )
    expected = {
        "proxy_user_id": "alice_residential",
        "available_bandwidth": 10737418240,
    }
    if params is not None:
        expected["residential_params"] = params
    assert result.model_dump(exclude_none=True) == expected
    user_repository.get_user.assert_called_once_with("alice_residential")


@pytest.mark.parametrize(
    "failure, message",
    [
        ("missing_user", "user not found"),
        ("wrong_password", "invalid password"),
        ("zero_bandwidth", "no available bandwidth"),
    ],
)
def test_authentication_failures(failure, message, user, user_repository):
    password = "secretpass123"
    if failure == "missing_user":
        user_repository.get_user.return_value = None
    elif failure == "wrong_password":
        password = "wrong"
    else:
        user.proxy_user_available_bandwidth = 0

    with pytest.raises(ValueError, match=f"^{message}$"):
        AuthService(user_repository).authenticate("alice_residential", password)
