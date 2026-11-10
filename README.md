# EdTech / Nomera Backend API

A production-grade, modular monolith REST API powering the Nomera School ERP platform. Built with Python 3.12, FastAPI, SQLAlchemy 2 (Async), PostgreSQL, and Alembic.

---

## 1. Purpose

The backend provides a secure, auditable, and high-performance core for school management operations, including:
- **Authentication & Security:** JWT session management with refresh token rotation, RFC 6238 TOTP MFA, account lockout, and role-based access control (RBAC).
- **Academic Management:** Classes, sections, subjects, timetables, lesson plans, chapter notes, and attendance tracking.
- **Exams & Grading:** Exam creation, subject marks entry, report card generation, and state/CBSE mark conversion calculators.
- **Financial Operations:** Fee structure definitions, student invoicing, idempotent payment recording, late fee calculations, scholarships, and payroll processing.
- **Hostel & Logistics:** Room/bed allocations, mess expense tracking, maintenance tickets, bus fleet management, and student transport allocations.
- **Observability:** Structured JSON logging, `X-Request-ID` correlation, unified response envelope, and audit logging.

---

## 2. Architecture & Standards

- **API Versioning:** All domain endpoints are mounted under `/api/v1/...` (e.g., `/api/v1/students`, `/api/v1/auth/login`).
- **Response Envelope:** Standard `{ success, data, error, meta }` response shape with request correlation IDs and UTC ISO timestamps.
- **Strict Input Validation:** All request payloads strictly validated via Pydantic schemas enforcing `ConfigDict(extra="forbid")` to prevent mass-assignment.
- **Database Schema:** 91 tables with explicit primary keys, foreign key constraints with B-tree indexes, and reversible Alembic migrations.

For architecture decisions, consult the records under [`docs/adr/`](./docs/adr/).

---

## 3. Setup & Installation

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ (local service or Docker container)

### Local Environment Setup

1. **Clone the repository and navigate to backend directory:**
   ```bash
   cd be/EdTech_backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install pinned dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example environment template and configure your local settings:
   ```bash
   cp .env.example .env
   ```
   *(Note: Never commit `.env` or production credentials. Use local placeholders).*

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

---

## 4. Running the Application

### Local Development Server
Start the FastAPI server with live reloading:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- Health Check Probe: `http://localhost:8000/health`

### Local Docker Compose
To run both the application and a local PostgreSQL container orchestrated:
```bash
docker compose up --build
```

---

## 5. Testing

The backend includes a comprehensive test suite of 90 unit and integration tests covering authentication, route authorization guards, schema validation, rate limiting, pagination, idempotency, and foreign key indexes.

### Run All Tests
```bash
pytest -v
```

### Run With Test Isolation
Rate limiter state is automatically purged between test runs via an autouse fixture in `tests/conftest.py`:
```bash
pytest tests/unit/test_rate_limit.py -v
```

### Code Quality & Linting
Run the configured Ruff linter and formatter:
```bash
ruff check .
ruff format --check .
```

---

## 6. Deployment

### Multi-Stage Hardened Docker Container
The included production `Dockerfile` enforces security best practices:
- Multi-stage build minimizing image footprint.
- Runs under an unprivileged non-root user (`appuser`, UID `10001`).
- Built-in container healthcheck probe.
- Exposes port `8000`.

Build and run the production image:
```bash
docker build -t edtech-backend:latest .
docker run -p 8000:8000 --env-file .env edtech-backend:latest
```

### Local superadmin demonstration account

The optional demo account is disabled by default and is rejected unless the backend is running in `development` or `local` mode. To enable it, set these values in the backend's uncommitted `.env` file:

```dotenv
ENVIRONMENT=development
ENABLE_DEMO_SUPERADMIN=true
DEMO_SUPERADMIN_EMAIL=your-demo-email@example.com
DEMO_SUPERADMIN_PASSWORD=use-a-local-demo-password-of-at-least-12-characters
```

Apply migrations, then restart the backend. Startup creates the account only if that email is unused; it hashes the password and assigns the existing `SUPER_ADMIN` role. Existing users are never promoted or have their password changed. Set `ENABLE_DEMO_SUPERADMIN=false` after the demo to block this account from new logins. Never enable this feature in production.
