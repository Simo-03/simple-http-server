# Auth and proxy routing server

A FastAPI service implementing the auth and routing pipeline in [SPEC.md](SPEC.md).
`POST /auth` validates credentials and extracts location preferences from a username.
`POST /route` uses the returned context and a protocol to select a proxy.

## Requirements

- Python 3.13 or later and `uv`.
- Docker with Docker Compose for the supplied PostgreSQL database.
- PostgreSQL's `libpq` client library, required by the standard `psycopg` package.

## Setup and run

Run these commands from the repository root. Choose an available HTTP port;
`8000` below is an example:

```bash
uv sync --locked
# Create .env if it does not already exist.
test -f .env || cp .env.example .env

docker compose up -d
docker compose exec -T postgres pg_isready -U ping_dev -d ping_residential

APP_PORT=8000
uv run uvicorn src.main:app --host 127.0.0.1 --port "$APP_PORT"
```

If PostgreSQL is still starting, repeat the readiness check after a few seconds.
The `.env.example` connection matches the Compose database:

```dotenv
DATABASE_URL=postgresql://ping_dev:localdev@localhost:5432/ping_residential?sslmode=disable
```

`init.sql` creates the tables and seed data when the database directory is first
initialized. Restarting an existing database does not reapply it.

Open `http://127.0.0.1:<port>/docs`, replacing `<port>` with your chosen port, to
try the endpoints. Add `--reload` to the Uvicorn command during development.
Stop the server with Ctrl+C and the database with `docker compose stop`.

## Example: authenticate, then route

In a second terminal, set `APP_PORT` to the same port used by the server. Then
authenticate the seeded Alice user, requesting a US proxy in New York:

```bash
APP_PORT=8000  # Use the port you selected above.
APP_BASE_URL="http://127.0.0.1:${APP_PORT}"

curl -sS -X POST "${APP_BASE_URL}/auth" \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice_residential_c_us_city_new_york","password":"secretpass123"}'
```

The HTTP 200 response contains the user's ID, bandwidth, and parsed country/city
inside `context.auth_service`. Pass that context to `/route`:

```bash
curl -sS -X POST "${APP_BASE_URL}/route" \
  -H 'Content-Type: application/json' \
  -d '{"context":{"auth_service":{"proxy_user_id":"alice_residential","available_bandwidth":10737418240,"residential_params":{"country":"us","city":"new_york"}}},"protocol":"http"}'
```

With the seed data, this returns `192.168.1.1:8080`. The response preserves the auth
context, adds `context.route_service`, and repeats the selected `proxy_addr` at
the top level. Changing the protocol to `socks5` falls back to another US proxy,
`192.168.1.3:1080`, because New York has no compatible SOCKS5 proxy.

The username format is `<proxy_user_id>[_c_<country>[_city_<city>]]`:

- `alice_residential`: select from any location supporting the protocol.
- `alice_residential_c_gb`: select within Great Britain.
- `alice_residential_c_us_city_new_york`: try New York, then another US proxy.

City requires country. Routing never falls back to a different country. Every
lookup filters by `http` or `socks5`, and randomly selects one eligible proxy.
The seed addresses are sample records; this service does not forward traffic.

## Errors

Error responses use this shape, with the HTTP status sent separately:

```json
{"internal_error_code": 1001, "error_message": "invalid password"}
```

| Source | HTTP status | Internal code | Message |
| --- | ---: | ---: | --- |
| Auth | 400 | 1000 | `invalid username format` |
| Auth | 401 | 1001 | `invalid password` |
| Auth | 403 | 1002 | `no available bandwidth` |
| Auth | 401 | 1003 | `user not found` |
| Route | 400 | 3001 | `unsupported protocol` |
| Route | 404 | 3400 | `no proxy found for country` |
| Request validation | 400 | 4000 | `invalid request body` |
| Framework HTTP errors | Original status, e.g. 404/405 | 4001 | Framework message, e.g. `Not Found` |
| Unexpected failures | 500 | 5000 | `internal server error` |

Codes **4000, 4001, and 5000** extend the specification. Unexpected failures are
logged with their traceback; exception details are omitted from the response.
Error 3400 also covers untargeted requests with no protocol-compatible proxies.

## Tests

```bash
uv run pytest
uv run ruff check .
```

The suite contains 69 test cases covering username parsing, authentication failures,
routing and fallback, context preservation, exact HTTP responses, validation, and
exception formatting. Tests use mocked repositories and require neither Docker nor
a running server. Ruff checks the Python source and tests for lint issues.

## Assumptions

- `/route` receives context from a trusted internal caller and does not authenticate
  again or recheck bandwidth in the database.
- Bandwidth is returned in bytes. These endpoints do not consume or reserve it.
- User IDs contain ASCII letters, digits, and underscores. `_c_` and `_city_` are
  reserved delimiters. City names contain lowercase alphabetic words separated
  by single underscores. These are parser assumptions beyond the spec's examples.
- Country codes must contain exactly two lowercase letters and exist in
  `pycountry`'s ISO country data. Invalid codes return HTTP 400 with code 1000.
  Valid countries without matching proxies authenticate normally; routing then
  returns HTTP 404 with code 3400.
- Passwords are compared as plaintext to match the supplied seed data.
- Context preservation covers the declared schema fields; unknown fields are ignored.

## Trade-offs and future improvements

- **Code structure:** HTTP handlers, business services, and database repositories
  have separate responsibilities.
- **Database sessions:** SQLAlchemy provides a shared connection pool and a
  session per request.
- **Proxy selection:** Selection uses `ORDER BY random() LIMIT 1`. At scale, query
  indexes and an eligible-proxy pool or cache would reduce selection work.
- **Additional routing rules:** State targeting could extend the service's
  fallback policy. Per-user rate limiting could be added as a separate stage.
- **Passwords:** Password hashing would replace plaintext comparison in a
  production implementation.
- **Logging:** SQL logging is enabled for development. Structured request logs
  would improve operational visibility.
- **Database storage:** An attached persistent data volume would provide durable
  local storage across container removal.
