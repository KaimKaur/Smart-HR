# Smart HR

AI-powered Human Resource Management platform — modular monolith with **FastAPI**, **PostgreSQL 16**, and **Next.js 15**.

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Backend | FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic v2, python-jose, Argon2 |
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui, TanStack Query |
| Data | PostgreSQL 16 |
| AI | spaCy, scikit-learn, OpenAI-compatible API |
| Ops | Docker, Nginx, GitHub Actions |

## Repository layout

```text
├── backend/                 # FastAPI application
├── frontend/                # Next.js application
├── infrastructure/          # Dockerfiles, nginx, scripts
│   ├── docker/
│   ├── nginx/
│   └── scripts/
├── docs/                    # Specifications and implementation memory
├── docker-compose.yml       # Local development (hot reload)
├── docker-compose.prod.yml  # Production stack
└── .env.example             # Environment template
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+ with Compose v2
- Optional (native dev): Python 3.12+, Node.js 20+, PostgreSQL 16

## Quick start (Docker — recommended)

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
DATABASE_URL=postgresql+asyncpg://smart_hr:smart_hr_dev@db:5432/smart_hr
JWT_SECRET_KEY=change-me-to-a-long-random-string-min-32-chars
JWT_REFRESH_SECRET_KEY=change-me-to-another-long-random-string
```

Generate secrets (example):

```bash
openssl rand -hex 32
```

### 2. Start the full stack

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 |
| OpenAPI docs | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` (user/db from `.env`) |

### 3. Run migrations and seed (first run)

In a second terminal:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

Bootstrap administrator:

| Field | Value |
|-------|-------|
| Email | `admin@smarthr.dev` |
| Password | `ChangeMe123!` |
| Role | `system_administrator` |

## Local development (without Docker)

### Database only

```bash
docker compose up -d db
```

Set `DATABASE_URL=postgresql+asyncpg://smart_hr:smart_hr_dev@localhost:5432/smart_hr` in `.env`.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m spacy download en_core_web_sm
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `.env` (or `.env.local`).

## Environment variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://smart_hr:smart_hr_dev@db:5432/smart_hr` | Async SQLAlchemy URL |
| `JWT_SECRET_KEY` | Yes | (32+ char random) | Access token signing secret |
| `JWT_REFRESH_SECRET_KEY` | Yes | (32+ char random) | Refresh token signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `PASSWORD_RESET_EXPIRE_HOURS` | No | `24` | Reset token TTL |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated origins |
| `POSTGRES_USER` | No | `smart_hr` | Docker DB user |
| `POSTGRES_PASSWORD` | No | `smart_hr_dev` | Docker DB password |
| `POSTGRES_DB` | No | `smart_hr` | Docker DB name |
| `NEXT_PUBLIC_API_BASE_URL` | No | `http://localhost:8000/api/v1` | Browser API base URL |
| `RESUME_UPLOAD_DIR` | No | `uploads/resumes` | Resume storage path |
| `OPENAI_API_KEY` / `AI_*` | No | — | AI screening (optional) |

See [.env.example](.env.example) for the full list.

## Migrations

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Inside Docker:

```bash
docker compose exec backend alembic upgrade head
```

## Seeding

Idempotent — safe to run multiple times:

```bash
cd backend && python scripts/seed.py
# or
docker compose exec backend python scripts/seed.py
```

## Tests

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
python -m spacy download en_core_web_sm
pytest
```

Coverage HTML report: `backend/htmlcov/index.html`

### Frontend

```bash
cd frontend
npm ci
npm run test
npm run lint
npm run typecheck
```

CI runs the same checks on pull requests (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Production deployment

### Build production images

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Production stack includes **Nginx** on port `80` (configurable via `HTTP_PORT`):

- `/api/v1/*` → backend
- all other paths → frontend
- security headers and gzip enabled ([infrastructure/nginx/nginx.conf](infrastructure/nginx/nginx.conf))

The database service is **not** published to the host. Backend waits for a healthy database before starting.

### GitHub Actions CD

On merge to `main`, [.github/workflows/deploy.yml](.github/workflows/deploy.yml):

1. Builds and pushes images to `ghcr.io/<owner>/<repo>/backend` and `.../frontend` tagged with the commit SHA and `latest`
2. SSH deploys to the server (when secrets are configured)

Required repository secrets:

| Secret | Purpose |
|--------|---------|
| `SSH_HOST` | Target server hostname |
| `SSH_USER` | SSH user |
| `SSH_PRIVATE_KEY` | Private key for SSH |
| `DEPLOY_PATH` | Directory on server (e.g. `/opt/smart-hr`) |

Remote deploy runs:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
```

### Rollback

Redeploy a known-good image tag on the server:

```bash
cd /opt/smart-hr
export BACKEND_IMAGE=ghcr.io/<owner>/<repo>/backend:<previous-sha>
export FRONTEND_IMAGE=ghcr.io/<owner>/<repo>/frontend:<previous-sha>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Keep the previous SHA from GitHub Actions run history or container registry tags.

## Database backup

Cron-friendly script: [infrastructure/scripts/backup.sh](infrastructure/scripts/backup.sh)

```bash
chmod +x infrastructure/scripts/backup.sh
POSTGRES_PASSWORD=smart_hr_dev ./infrastructure/scripts/backup.sh
```

Produces `backups/smart_hr_YYYYMMDD_HHMMSS.sql.gz`.

**Restore** (plain SQL dump):

```bash
gunzip -c backups/smart_hr_YYYYMMDD_HHMMSS.sql.gz | psql \
  "postgresql://smart_hr:smart_hr_dev@localhost:5432/smart_hr"
```

For custom-format dumps, use `pg_dump -Fc` and restore with `pg_restore` (see script header comments).

Example cron (daily at 02:00 UTC):

```cron
0 2 * * * POSTGRES_PASSWORD=... /opt/smart-hr/infrastructure/scripts/backup.sh
```

## Documentation

| Document | Path |
|----------|------|
| Product requirements | [docs/PRD.md](docs/PRD.md) |
| System architecture | [docs/architecture.md](docs/architecture.md) |
| REST API contract | [docs/API.md](docs/API.md) |
| Database schema | [docs/schema.sql](docs/schema.sql) |
| Implementation plan | [docs/ImplementationPlan.md](docs/ImplementationPlan.md) |
| Architecture rules | [docs/PROJECT_KERNEL.md](docs/PROJECT_KERNEL.md) |

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software under the terms of the GPLv3 license.

See the LICENSE file for details.