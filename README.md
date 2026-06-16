# Michelin Riding API

FastAPI backend for the Michelin Riding app, with a MySQL database. Both services run in Docker.

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting started

### 1. Clone and configure

Copy the example env file and adjust values if needed:

```bash
cp .env.example .env
```

### 2. Start the services

```bash
docker compose up --build
```

This starts two containers:
- **api** — FastAPI on `http://localhost:8000`
- **db** — MySQL 8.0 on port `3306`

The API waits for the database to be healthy before starting.

### 3. Run database migrations

On first run (and after any model change), apply the migrations:

```bash
docker compose exec api alembic upgrade head
```

To generate a new migration after changing a model:

```bash
docker compose exec api alembic revision --autogenerate -m "describe your change"
docker compose exec api alembic upgrade head
```

### 4. Explore the API

Interactive docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

Health check:

```bash
curl http://localhost:8000/health
```

## Authentication

All endpoints except `/auth/register` and `/auth/login` require a Bearer token.

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","password":"StrongPass1!"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"StrongPass1!"}'

# Use the returned access_token in subsequent requests
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Running tests

Make sure the app is running (`docker compose up`), then:

```bash
docker compose exec api pip install pytest httpx
docker compose exec api python -m pytest tests/ -v
```

## Stopping the app

```bash
docker compose down
```

To also delete the database volume:

```bash
docker compose down -v
```

## Project structure

```
.
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings from .env
│   ├── database.py          # Async SQLAlchemy engine and session
│   ├── core/
│   │   └── security.py      # JWT creation, password hashing, auth dependency
│   ├── models/
│   │   └── models.py        # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   └── routers/             # One file per tag (auth, profiles, activities…)
├── alembic/                 # Database migrations
├── tests/
│   ├── conftest.py          # Shared fixtures
│   └── test_api.py          # Integration tests (41 tests)
├── Dockerfile
├── docker-compose.yml
└── .env
```

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async connection string | `mysql+aiomysql://appuser:apppassword@db:3306/appdb` |
| `SECRET_KEY` | JWT signing secret | change in production |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` (24 h) |
| `MYSQL_DATABASE` | Database name | `appdb` |
| `MYSQL_USER` | DB user | `appuser` |
| `MYSQL_PASSWORD` | DB password | `apppassword` |
| `MYSQL_ROOT_PASSWORD` | DB root password | `rootpassword` |
