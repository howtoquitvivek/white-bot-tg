# Telegram Video Bot — Core Foundation

Production-minded, asynchronous, modular foundation for an adult media distribution Telegram bot built with **Python 3.12**, **aiogram 3.x**, **PostgreSQL**, **SQLAlchemy 2.x (asyncpg)**, and **Alembic**.

## Project Overview

This repository provides the core architectural foundation for an authorized video distribution bot on Telegram. It implements:
- Clean modular monolithic design (`app/` package).
- Environment validation with sensitive secret masking using `pydantic-settings`.
- Strict access-gating flow with 18+ age confirmation.
- Asynchronous database engine, connection checking, and session lifecycle management.
- Idempotent user registration tracking Telegram identity.
- Database schema management via Alembic migrations.
- Unit and integration tests (using an in-memory SQLite async test database, requiring no external credentials).

> [!NOTE]
> All content distributed via this architecture must be lawful, consensually produced, and authorized for distribution. The age confirmation mechanism acts as an access gate and does not constitute formal legal identity verification.

> [!TIP]
> **Single-Click Local Development:** You can launch the entire stack (FastAPI Backend, Vite Admin Dashboard, and Telegram Bot) with a single command:
> ```bash
> ./run_dev.sh
> # or
> ./dev.sh
> ```
> See the dedicated [RUNNING.md](file:///home/howtoquitvivek/tg-bot/RUNNING.md) guide for details.

---

## Architecture and Project Structure

```
tg-bot/
├── app/
│   ├── __init__.py           # Package marker
│   ├── config.py             # Pydantic Settings & environment validation
│   ├── bot.py                # Bot, Dispatcher, and DB session middleware
│   ├── main.py               # Application entrypoint & graceful lifecycle
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── start.py          # /start command, age gate callbacks, menu stubs
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── main_menu.py      # Inline age-gate and persistent reply keyboards
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py           # DeclarativeBase with AsyncAttrs
│   │   └── session.py        # Async engine, sessionmaker, ping & disposal
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py           # SQLAlchemy User entity (UUID, BigInt, TZ datetimes)
│   └── services/
│       ├── __init__.py
│       └── user_service.py   # Idempotent registration and age confirmation
├── migrations/
│   ├── env.py                # Async Alembic migration runner
│   ├── script.py.mako
│   └── versions/
│       └── 001_create_users_table.py # Initial users table schema
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Async SQLite fixtures & isolated test sessions
│   ├── test_config.py        # Config validation and secret masking tests
│   ├── test_handlers.py      # Bot /start and callback interaction tests
│   └── test_user_service.py  # User CRUD, idempotency & age gating tests
├── .env                      # Local environment configuration (uncommitted)
├── .env.example              # Example environment configuration template
├── .gitignore                # Production git ignore rules
├── alembic.ini               # Alembic database migration config
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
├── RUNNING.md                # Running & deployment instructions
└── README.md                 # Project documentation
```

---

## Prerequisites

- **OS:** Linux or WSL (Windows Subsystem for Linux, Ubuntu 22.04+ recommended)
- **Python:** Python 3.12 or higher (`python3 --version`)
- **Package Manager:** `pip` (`pip3 --version`)
- **Database:** PostgreSQL 14+ server

---

## Setup Guide (WSL / Linux)

### 1. PostgreSQL Installation & Database Creation

If PostgreSQL is not yet installed in your WSL environment, install it using `apt`:

```bash
# Update package index and install PostgreSQL with contrib package
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Verify PostgreSQL is running
sudo service postgresql status
```

Create the application database and configure a secure password:

```bash
# Switch to the postgres system user and open psql
sudo -u postgres psql
```

Inside the `psql` console, run:

```sql
-- Set password for the postgres user (or create a dedicated user)
ALTER USER postgres WITH PASSWORD 'your_secure_password';

-- Create the database
CREATE DATABASE video_bot;

-- Verify database creation
\l

-- Exit psql
\q
```

---

### 2. Python Virtual Environment

Navigate to the project root directory and create the virtual environment:

```bash
cd /home/howtoquitvivek/tg-bot

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip
```

---

### 3. Dependency Installation

Install the required production and test dependencies:

```bash
pip install -r requirements.txt
```

---

### 4. Bot Token Configuration (@BotFather)

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to create your bot.
3. BotFather will provide an API token in the format `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`.

---

### 5. Environment Variables Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your actual bot token and PostgreSQL credentials:

```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@localhost:5432/video_bot
LOG_LEVEL=INFO
```

> [!CAUTION]
> Never commit `.env` or share your `BOT_TOKEN`. The `.gitignore` file is configured to exclude all `.env` files.

---

### 6. Database Migrations (Alembic)

Once your PostgreSQL database is running and configured in `.env`, apply migrations:

```bash
# Apply all pending migrations to head
alembic upgrade head
```

To inspect generated SQL without connecting to the database (offline mode):

```bash
alembic upgrade head --sql
```

To roll back a migration:

```bash
alembic downgrade -1
```

---

### 7. Running the Bot

Run the application:

```bash
python -m app.main
```

When started, the application will:
1. Validate required environment variables.
2. Verify PostgreSQL connectivity with a ping check.
3. Register the database session middleware and handlers.
4. Drop stale webhook updates and begin long polling.

To stop the bot gracefully, press `Ctrl + C`. The engine connection pool and HTTP session will close cleanly.

---

### 8. Running Tests

The test suite uses an in-memory SQLite async engine (`sqlite+aiosqlite:///:memory:`). No active PostgreSQL instance or live Telegram bot token is required to execute tests.

```bash
# Run all unit and integration tests
pytest -v

# Run with coverage report
pytest --tb=short
```

---

## Bot Interaction Flow

1. **Initial Start (`/start`):**
   - User is idempotently looked up or inserted into the `users` table.
   - If `age_verified_at` is `NULL`, the bot responds with an 18+ access gate prompt and inline buttons:
     - `🔞 I am 18 or older`
     - `❌ Exit`
2. **Age Confirmation:**
   - User clicks `🔞 I am 18 or older`.
   - The callback is validated server-side.
   - A timezone-aware UTC timestamp (`age_verified_at`) is persisted to PostgreSQL.
   - The user receives access to the main menu keyboard:
     - `🎬 Browse Videos`
     - `📁 Collections`
     - `ℹ️ Help`
3. **Exit:**
   - User clicks `❌ Exit`.
   - The bot records no confirmation, informs the user access is restricted, and does not reveal the main menu.

---

## Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `Configuration validation failed: Field 'BOT_TOKEN'` | Placeholder or missing token in `.env` | Put your real token from @BotFather into `.env`. |
| `Database connectivity check failed: [Errno 111] Connect call failed` | PostgreSQL is stopped or wrong port | Run `sudo service postgresql start` and check port `5432`. |
| `FATAL: password authentication failed for user "postgres"` | Incorrect password in `DATABASE_URL` | Run `sudo -u postgres psql` and update password via `ALTER USER postgres WITH PASSWORD '...';`. |
| `ModuleNotFoundError: No module named 'greenlet'` | Virtual environment missing greenlet | Run `pip install greenlet`. |

---

## Scope & Future Roadmap

- **Phase 1 (Completed):** Modular monolith structure, async PostgreSQL connection, Alembic migrations, idempotent user tracking, 18+ age gating flow, and test suite.
- **Phase 2 (Upcoming):** Video catalog indexing, category filters, and collection browsing.
- **Phase 3 (Upcoming):** Secure content delivery and rate limiting.

