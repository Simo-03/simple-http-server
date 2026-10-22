# Automated tests

From the project root, install dependencies and run the suite:

```bash
uv sync
uv run pytest
```

Service and HTTP tests run without Docker, a running server, or a `.env` file.
The HTTP tests use FastAPI's TestClient with fake repositories while retaining
the real handlers, services, request validation, and response serialization.
They cover authentication, username parsing, routing/fallback, context preservation,
the specified error responses, and invalid request bodies.

## Test inventory

There are **69 cases**. Parameterized tests run once for each listed input.

| File / group | Cases | What is checked |
| --- | ---: | --- |
| Auth service: valid username parsing | 4 | Plain ID, ID with digits/underscores, country, country plus city |
| Auth service: invalid usernames | 11 | Empty input; hyphen/space in ID; city without country; empty ID; empty, uppercase, or overlong country; empty, uppercase, or double-underscore city |
| Auth service: successful authentication | 3 | Correct user/bandwidth and omitted optional fields for no targeting, country, and country plus city |
| Auth service: failures | 3 | Missing user, wrong password, zero bandwidth |
| Route service: successful selection | 5 | HTTP/SOCKS5 exact targeting, country-only targeting, untargeted HTTP/SOCKS5; correct lookup arguments and serialized address |
| Route service: city fallback | 2 | HTTP and SOCKS5 retries retain country and protocol while dropping city |
| Route service: no proxy | 3 | City-plus-country miss, country-only miss, untargeted miss; no widening to a different country |
| Route service: unsupported protocols | 4 | `ftp`, `HTTP`, `SOCKS5`, and empty string fail before a repository lookup |
| HTTP: auth success | 3 | Exact 200 response for no targeting, country, and country plus city |
| HTTP: auth errors | 4 | Exact status, internal code, and body for errors 1000, 1001, 1002, and 1003 |
| HTTP: auth-to-route workflows | 5 | Exact match, city fallback, country only, untargeted HTTP, untargeted SOCKS5; exact response and retained auth context |
| HTTP: route errors | 4 | Unsupported protocol; no proxy for country, city/fallback, or untargeted request |
| HTTP: invalid request structures | 7 | Empty auth/route bodies, missing password, numeric username, missing protocol, missing auth context, null auth context |
| HTTP: malformed JSON | 2 | Both endpoints return HTTP 400 with code 4000 and the exact body |
| HTTP: unexpected service errors | 2 | Both handlers re-raise an unknown `ValueError` instead of mislabeling it as a known business error |
| HTTP: framework errors | 3 | Unknown URL returns 404/4001; GET on `/auth` and `/route` returns 405/4001 and preserves the `Allow: POST` header |
| HTTP: unexpected failure responses | 4 | `ValueError` and `RuntimeError` on both endpoints return generic 500/5000 JSON while logging the original exception, traceback, method, and path |

Malformed usernames are rejected before a repository lookup. The test cases that
reject double underscores in cities enforce the current parser assumption; the
specification does not explicitly require that restriction.

The saved suite uses mocked repositories and does not verify SQL execution,
PostgreSQL `INET` adaptation, or random-selection distribution. There are no
PostgreSQL tests in the suite.

Useful narrower commands:

```bash
uv run pytest tests/test_route_service.py -v
uv run pytest tests/test_api.py -v
```
