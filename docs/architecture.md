# StartupInfo — Architecture Document

> **Living document.** Update this file with every PR that changes the stack, schema, or project structure.
> Last updated: 2026-03-31

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure](#3-repository-structure)
4. [Backend Architecture](#4-backend-architecture)
5. [Database Schema](#5-database-schema)
6. [API Reference](#6-api-reference)
7. [Authentication](#7-authentication)
8. [Discovery Service](#8-discovery-service)
9. [iOS App Architecture](#9-ios-app-architecture)
10. [Infrastructure & Deployment](#10-infrastructure--deployment)
11. [How to Run Locally](#11-how-to-run-locally)
12. [How to Run Tests](#12-how-to-run-tests)
13. [Environment Variables](#13-environment-variables)

---

## 1. System Overview

StartupInfo is a mobile-first iOS application that lets users research startups, trace their
investor networks, discover additional portfolio companies, and track job applications — all
from one place.

```
┌─────────────────────┐        HTTPS/JSON       ┌──────────────────────────┐
│   iOS App (SwiftUI) │ ◄──────────────────────► │  REST API  (FastAPI)     │
│   iOS 15+           │                          │  Python 3.12 / uvicorn   │
└─────────────────────┘                          └──────────┬───────────────┘
                                                            │
                                          ┌─────────────────┼──────────────────┐
                                          │                 │                  │
                                 ┌────────▼───────┐  ┌──────▼──────┐  ┌───────▼──────┐
                                 │  PostgreSQL 16 │  │  Discovery  │  │  Audit Log   │
                                 │  (Supabase /   │  │  Service    │  │  (DB trigger)│
                                 │   local Docker)│  │  + DuckDuckGo│  └──────────────┘
                                 └────────────────┘  └─────────────┘
```

---

## 2. Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| iOS Frontend | Swift + SwiftUI | iOS 15+ target | MVVM, no offline mode in v1 |
| REST API | Python + FastAPI | 3.12 / 0.111+ | ASGI via uvicorn |
| ORM | SQLAlchemy 2 | 2.0+ | Async via asyncpg |
| Migrations | Alembic | 1.13+ | Version-controlled, reviewed in PR |
| Database | PostgreSQL | 16 | JSONB for metadata, full ACID |
| Auth | bcrypt + JWT | passlib / python-jose | Username/password v1; OAuth future |
| Web Search | DuckDuckGo (duckduckgo-search) | Python library | Free, no API key, confirmed for v1 |
| Job Discovery | BeautifulSoup + Playwright | 4.x / 1.x | Career page scraping |
| Background Tasks | FastAPI BackgroundTasks | built-in | Celery in v2 if needed |
| Containerisation | Docker + Docker Compose | 24+ | Single-command local dev |
| Cloud (API) | Railway or Render | — | Free/low-cost tier |
| Cloud (DB) | Supabase | — | Free tier (500 MB) |
| CI/CD | GitHub Actions | — | Lint + test on every PR |
| Logging | structlog | 24+ | Structured JSON to stdout |

---

## 3. Repository Structure

```
startupinfo/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   ├── dependencies.py       # Shared FastAPI dependencies (DB session, current user)
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── company.py
│   │   │   ├── investor.py
│   │   │   ├── investment.py
│   │   │   ├── job.py
│   │   │   ├── job_application.py
│   │   │   └── audit_log.py
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── company.py
│   │   │   ├── investor.py
│   │   │   ├── investment.py
│   │   │   ├── job.py
│   │   │   └── job_application.py
│   │   ├── api/                  # FastAPI routers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── companies.py
│   │   │   ├── investors.py
│   │   │   ├── investments.py
│   │   │   ├── jobs.py
│   │   │   └── applications.py
│   │   └── services/             # Business logic
│   │       ├── __init__.py
│   │       ├── auth.py           # Password hashing, JWT
│   │       ├── company.py
│   │       ├── investor.py
│   │       └── discovery/
│   │           ├── __init__.py
│   │           ├── serp.py       # DuckDuckGo search client
│   │           ├── company.py    # Company discovery task
│   │           ├── investor.py   # Investor portfolio discovery
│   │           └── jobs.py       # Career page scraper
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/             # One file per migration
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_companies.py
│   │   ├── test_investors.py
│   │   ├── test_investments.py
│   │   └── test_applications.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── alembic.ini
├── ios/
│   └── StartupInfo/              # Xcode project (added when iOS dev starts)
├── infra/
│   ├── docker-compose.yml
│   └── .env.example
├── docs/
│   ├── StartupInfo.spec.v.0.md
│   ├── StartupInfo_Implementation_Plan.docx
│   └── architecture.md           ← this file
└── .github/
    └── workflows/
        ├── backend-ci.yml
        └── ios-ci.yml
```

---

## 4. Backend Architecture

### Request lifecycle

```
Request
  └─► FastAPI router (api/)
        └─► Dependency injection (dependencies.py)
              ├─► DB session (AsyncSession)
              └─► Current user (JWT decode)
                    └─► Service layer (services/)
                          ├─► SQLAlchemy ORM queries
                          └─► Background task dispatch (discovery/)
                                └─► DuckDuckGo / Playwright
                                      └─► DB upsert + audit_log
```

### Key design principles

- **Service layer owns logic.** Routers are thin — they validate input and call services.
- **Async throughout.** All DB I/O uses `AsyncSession`; all HTTP calls use `httpx.AsyncClient`.
- **Upsert, don't duplicate.** Discovery tasks use `INSERT ... ON CONFLICT DO UPDATE`.
- **Audit every mutation.** A PostgreSQL trigger writes to `audit_log` on every INSERT/UPDATE/DELETE across all business tables.
- **Background tasks are fire-and-forget in v1.** The iOS app polls a status field (`companies.status`) to know when discovery completes.

---

## 5. Database Schema

### Entity-Relationship Summary

```
users (1) ──────────────────────────── (many) job_applications
companies (1) ──── (many) investments ──── (many) investors
companies (1) ──── (many) jobs ──── (many) job_applications
All tables ──────────────────────────────── (many) audit_log
```

### users
| Column | Type | Notes |
|---|---|---|
| user_id | UUID PK | auto-generated |
| username | TEXT UNIQUE NOT NULL | |
| email | TEXT UNIQUE NOT NULL | |
| password_hash | TEXT NOT NULL | bcrypt |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### companies
| Column | Type | Notes |
|---|---|---|
| company_name | TEXT PK | lowercase-trimmed canonical name |
| status | TEXT | stub \| discovering \| ready \| error |
| location | TEXT | |
| description | TEXT | |
| company_type | TEXT | public \| private \| acquired \| defunct |
| about | TEXT | |
| vision | TEXT | |
| mission | TEXT | |
| founders | TEXT[] | |
| website | TEXT | |
| linkedin_url | TEXT | |
| extra | JSONB | extensibility |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### investors
| Column | Type | Notes |
|---|---|---|
| investor_name | TEXT PK | |
| description | TEXT | |
| investor_type | TEXT | individual \| vc_firm \| corporate \| angel \| accelerator |
| total_companies_invested | INT | |
| total_amount_invested_usd | BIGINT | -1 if unknown |
| location | TEXT | |
| website | TEXT | |
| extra | JSONB | |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### investments *(3-column composite PK)*
| Column | Type | Notes |
|---|---|---|
| company_name | TEXT FK → companies | |
| investor_name | TEXT FK → investors | |
| series_name | TEXT | Seed, Series A, … |
| **PRIMARY KEY** | | (company_name, investor_name, series_name) |
| amount_invested_usd | BIGINT | -1 if unknown |
| investor_role | TEXT | lead \| participant \| angel |
| additional_comments | TEXT | |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### jobs
| Column | Type | Notes |
|---|---|---|
| job_id | UUID PK | auto |
| company_name | TEXT FK → companies | |
| title | TEXT | |
| location | TEXT | |
| job_type | TEXT | full_time \| part_time \| contract \| remote |
| url | TEXT | source posting URL |
| description | TEXT | |
| source | TEXT | scraped \| manual |
| is_active | BOOLEAN | soft-delete |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### job_applications
| Column | Type | Notes |
|---|---|---|
| application_id | UUID PK | auto |
| user_id | UUID FK → users | |
| job_id | UUID FK → jobs | |
| company_name | TEXT | denormalised for display |
| applied_date | DATE | |
| status | TEXT | wishlist \| applied \| phone_screen \| interview \| offer \| rejected \| withdrawn |
| notes | TEXT | |
| follow_up_date | DATE | optional |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### audit_log
| Column | Type | Notes |
|---|---|---|
| log_id | UUID PK | auto |
| table_name | TEXT | |
| record_pk | TEXT | |
| operation | TEXT | INSERT \| UPDATE \| DELETE |
| changed_by | TEXT | system \| user:<user_id> |
| old_values | JSONB | null for INSERT |
| new_values | JSONB | null for DELETE |
| occurred_at | TIMESTAMPTZ | auto |

---

## 6. API Reference

Base URL: `http://localhost:8000/api/v1`

All protected endpoints require: `Authorization: Bearer <jwt_token>`

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/register | ✗ | Register new user |
| POST | /auth/login | ✗ | Login → returns JWT |
| GET | /auth/me | ✓ | Current user profile |

### Companies
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /companies | ✓ | List (paginated, filter by status/type) |
| GET | /companies/{name} | ✓ | Company detail + investors |
| POST | /companies | ✓ | Create manually |
| PUT | /companies/{name} | ✓ | Update |
| POST | /companies/{name}/discover | ✓ | Trigger background discovery |

### Investors
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /investors | ✓ | List investors |
| GET | /investors/{name} | ✓ | Detail + portfolio |
| POST | /investors | ✓ | Create manually |
| PUT | /investors/{name} | ✓ | Update |
| POST | /investors/{name}/discover-portfolio | ✓ | Trigger portfolio discovery |

### Investments
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /companies/{name}/investments | ✓ | All rounds for a company |
| POST | /investments | ✓ | Add / upsert investment |
| PUT | /investments/{company}/{investor}/{series} | ✓ | Update investment |

### Jobs & Applications
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /jobs | ✓ | List jobs (filter company/location/type) |
| POST | /companies/{name}/jobs/discover | ✓ | Scrape careers page |
| GET | /applications | ✓ | My applications |
| POST | /applications | ✓ | Log application |
| PUT | /applications/{id} | ✓ | Update status / notes |

---

## 7. Authentication

**v1 — Username/Password + JWT**

1. `POST /auth/register` — stores `bcrypt`-hashed password in `users.password_hash`.
2. `POST /auth/login` — verifies password, returns a signed JWT (HS256, 7-day expiry).
3. Protected routes decode the JWT via `get_current_user` dependency.

**Future — Social Login**

The `users` table has an `extra JSONB` column reserved for OAuth provider fields
(`google_id`, `linkedin_id`, etc.). A future migration will add these columns without
breaking existing rows.

---

## 8. Discovery Service

Discovery runs as FastAPI `BackgroundTasks` in v1 (no separate worker process needed).

### Company discovery
```
discover_company(name)
  1. DuckDuckGo: search "{name} startup funding investors"
  2. Parse: founders, HQ, description, website, funding rounds
  3. Upsert → companies (status = "discovering" → "ready")
  4. For each investor found → upsert investors + investments
  5. For VC firm investors → queue discover_investor_portfolio()
```

### Investor portfolio discovery
```
discover_investor_portfolio(investor_name)
  1. DuckDuckGo: search "{investor_name} portfolio companies"
  2. For each company found → upsert companies (status = "stub")
```

### Job / careers page scraping
```
discover_jobs(company_name)
  1. Fetch company.website + "/careers" (try common paths)
  2. If JS-rendered → use Playwright headless browser
  3. BeautifulSoup parse → extract job title, location, type, URL
  4. Upsert → jobs; mark removed listings is_active=false
```

---

## 9. iOS App Architecture

- **Pattern:** MVVM
- **Minimum deployment:** iOS 15
- **Networking:** `URLSession` with `async/await`
- **No offline mode** in v1 — all data fetched live

### Screen hierarchy
```
TabBar
 ├── Search / Home
 │    └── Company List → Company Detail → Investor Detail
 ├── Jobs
 │    └── Job List → Job Detail → Log Application
 └── My Applications
      └── Application Detail (edit status, notes)
```

---

## 10. Infrastructure & Deployment

### Local (Docker Compose)
- `docker compose up` starts FastAPI (port 8000) + PostgreSQL (port 5432) + pgAdmin (port 5050).
- Live-reload enabled via volume mount.

### Cloud (Phase 2)
| Component | Service | Cost |
|---|---|---|
| Database | Supabase free tier | Free (500 MB) |
| API | Railway Starter / Render Free | ~$0–5/mo |
| Secrets | GitHub Actions Secrets | Free |
| Observability | Grafana Cloud free | Free |

Migration from local → cloud = **environment variable change only**, no code changes.

---

## 11. How to Run Locally

### Prerequisites
- Docker Desktop 4+
- Python 3.12 (for running tests outside Docker)
- `cp infra/.env.example infra/.env` and fill in your values

### Start everything
```bash
cd infra
docker compose up --build
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050

### Run migrations manually (inside backend container)
```bash
docker compose exec api alembic upgrade head
```

---

## 12. How to Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests use a separate test database spun up in the `conftest.py` fixture.
Fixture data includes: **ChatGPT (OpenAI)**, **Eridu**, **Anthropic** as example companies.

---

## 13. Environment Variables

See `infra/.env.example` for the full list. Key variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL async DSN (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Yes | JWT signing secret (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_DAYS` | No | JWT expiry in days (default: 7) |
| `LOG_LEVEL` | No | debug \| info \| warning (default: info) |
| `ENVIRONMENT` | No | local \| staging \| production |
