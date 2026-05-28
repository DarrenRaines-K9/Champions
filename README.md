# Champions in Christ

A volunteer coordination platform for community feeding events. Volunteers sign up for events, track food needs, and see who else is participating. Built with Django + DRF on the backend and Next.js 14 on the frontend.

Full architecture and decisions: [docs/implementation.md](docs/implementation.md) · [docs/decisions.md](docs/decisions.md)

---

## Quick Start

### Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+, pnpm, Docker

### Backend

```bash
cd backend
cp .env.example .env          # fill in values
docker compose -f ../docker-compose.yml up -d
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py create_coordinator_group
uv run python manage.py seed_data
uv run python manage.py runserver
```

Django runs at http://localhost:8000 · Admin at http://localhost:8000/admin

### Frontend

```bash
cd frontend
pnpm install
cp .env.local.example .env.local   # fill in values
pnpm dev
```

Next.js runs at http://localhost:3000

---

## Running Tests

```bash
cd backend
uv run pytest
```

---

## Database Backup

```bash
# Create a timestamped backup
docker exec champions-db-1 pg_dump -U champions champions > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i champions-db-1 psql -U champions champions < backup_YYYYMMDD_HHMMSS.sql
```

Run a backup before any risky migration or before re-seeding from scratch.

---

## Seed & Reset

```bash
uv run python manage.py seed_data    # populate realistic test data (idempotent)
uv run python manage.py flush_data   # wipe all data — dev only, requires DEBUG=True
```

---

## Architecture

Monorepo: `backend/` (Django + DRF) + `frontend/` (Next.js 14 App Router).

All authenticated API calls route through a Next.js server-side proxy — the Django access token never reaches browser JavaScript. See [ADR-002](docs/decisions.md#adr-002) for the full auth architecture.

---

## Contributing

Record all consequential architectural decisions as ADRs in [docs/decisions.md](docs/decisions.md) before writing the code that implements them.
