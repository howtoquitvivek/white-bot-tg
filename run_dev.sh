#!/usr/bin/env bash

# ==============================================================================
# Telegram Video Platform — Local Development Runner
# Starts PostgreSQL check, Alembic migrations, FastAPI backend,
# React Vite frontend, and the aiogram Telegram bot in a single terminal.
# ==============================================================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BOLD}${CYAN}======================================================${NC}"
echo -e "${BOLD}${CYAN}   🚀 Telegram Video Platform — Local Dev Environment ${NC}"
echo -e "${BOLD}${CYAN}======================================================${NC}"

# Handle --kill or -k flag to clean up previous processes
if [[ "$1" == "--kill" || "$1" == "-k" || "$1" == "--restart" || "$1" == "-r" ]]; then
    echo -e "${YELLOW}[CLEANUP] Stopping existing processes on ports 8000, 5173 and app.main...${NC}"
    fuser -k 8000/tcp 2>/dev/null || true
    fuser -k 5173/tcp 2>/dev/null || true
    pkill -f "python.*app\.main" 2>/dev/null || true
    sleep 1
fi

# 1. Check Python Virtual Environment
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
VENV_UVICORN="$SCRIPT_DIR/.venv/bin/uvicorn"
VENV_ALEMBIC="$SCRIPT_DIR/.venv/bin/alembic"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo -e "${YELLOW}[SETUP] Virtual environment not found. Creating .venv...${NC}"
    python3 -m venv "$SCRIPT_DIR/.venv"
    "$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip
    "$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# 2. Check Backend .env
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo -e "${YELLOW}[WARN] .env not found in project root. Copying from .env.example...${NC}"
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo -e "${RED}[ACTION REQUIRED] Please edit .env with your actual BOT_TOKEN and DATABASE_URL.${NC}"
    exit 1
fi

# 3. Check PostgreSQL Connectivity
echo -e "${BLUE}[CHECK] Verifying PostgreSQL connection...${NC}"
if command -v pg_isready >/dev/null 2>&1; then
    if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo -e "${YELLOW}[WARN] PostgreSQL service is not responding on localhost:5432.${NC}"
        echo -e "       Starting PostgreSQL via: sudo service postgresql start"
        sudo service postgresql start 2>/dev/null || true
    fi
fi

# Verify via Python Database Session
if ! "$VENV_PYTHON" -c "import asyncio; from app.config import get_settings; from app.database.session import init_db_engine, check_database_connection; settings = get_settings(); engine = init_db_engine(settings.DATABASE_URL); asyncio.run(check_database_connection(engine))" >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Could not connect to PostgreSQL using DATABASE_URL from .env.${NC}"
    echo -e "        Please ensure PostgreSQL is running and credentials in .env are correct."
    exit 1
fi
echo -e "${GREEN}[OK] PostgreSQL is connected and healthy.${NC}"

# 4. Run Alembic Database Migrations
echo -e "${BLUE}[MIGRATE] Checking database schema migrations...${NC}"
"$VENV_ALEMBIC" upgrade head >/dev/null 2>&1
echo -e "${GREEN}[OK] Database migrations are up to date.${NC}"

# 5. Check Frontend Dependencies
if [[ ! -d "$SCRIPT_DIR/frontend/node_modules" ]]; then
    echo -e "${YELLOW}[SETUP] Frontend node_modules missing. Installing npm packages...${NC}"
    (cd "$SCRIPT_DIR/frontend" && npm install)
fi

# 6. Clean up any stale instances on ports 8000 & 5173
free_project_ports() {
    local stale=false
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        stale=true
        fuser -k 8000/tcp >/dev/null 2>&1 || true
    fi
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
        stale=true
        fuser -k 5173/tcp >/dev/null 2>&1 || true
    fi
    if pgrep -fl "python.*app\.main" >/dev/null 2>&1; then
        stale=true
        pkill -f "python.*app\.main" >/dev/null 2>&1 || true
    fi
    if [ "$stale" = true ]; then
        echo -e "${YELLOW}[CLEANUP] Stopped previous instances on ports 8000/5173 for clean restart.${NC}"
        sleep 1
    fi
}
free_project_ports

# Array to keep track of spawned child process PIDs
PIDS=()

# Graceful cleanup on Ctrl+C (SIGINT) or exit
cleanup() {
    echo ""
    echo -e "${YELLOW}------------------------------------------------------${NC}"
    echo -e "${YELLOW}🛑 Stopping all services cleanly...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait "${PIDS[@]}" 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped. See you next time!${NC}"
    echo -e "${YELLOW}------------------------------------------------------${NC}"
}
trap cleanup SIGINT SIGTERM EXIT

# 7. Print Access Information
echo ""
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo -e "${BOLD}${GREEN}   🌟 Services Starting Successfully!                 ${NC}"
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo -e "  🌐 ${BOLD}Admin Web Dashboard:${NC}  ${CYAN}http://localhost:5173${NC}"
echo -e "  📖 ${BOLD}REST API Docs (Swagger):${NC} ${CYAN}http://localhost:8000/api/docs${NC}"
echo -e "  🩺 ${BOLD}API Health Endpoint:${NC}  ${CYAN}http://localhost:8000/api/health${NC}"
echo -e "  🤖 ${BOLD}Telegram Bot Polling:${NC} Active in background"
echo -e "  ⌨️  ${BOLD}Press Ctrl+C at any time to stop all services.${NC}"
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo ""

# Color-coded prefixes for logs
API_PREFIX="${CYAN}[API]${NC}  "
UI_PREFIX="${MAGENTA}[UI]${NC}   "
BOT_PREFIX="${GREEN}[BOT]${NC}  "

# Launch 1: FastAPI Backend
"$VENV_UVICORN" app.api.main:app --host 127.0.0.1 --port 8000 --reload 2>&1 | \
    sed -u "s/^/$(echo -e "$API_PREFIX")/" &
PIDS+=($!)

# Launch 2: Vite React Frontend
(cd "$SCRIPT_DIR/frontend" && npm run dev) 2>&1 | \
    sed -u "s/^/$(echo -e "$UI_PREFIX")/" &
PIDS+=($!)

# Launch 3: Telegram Bot
"$VENV_PYTHON" -m app.main 2>&1 | \
    sed -u "s/^/$(echo -e "$BOT_PREFIX")/" &
PIDS+=($!)

# Wait for all background jobs to finish or Ctrl+C
wait
