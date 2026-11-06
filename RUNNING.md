# Running Instructions — Telegram Video Platform

Comprehensive, step-by-step guide to configure, run, and operate the **Telegram Video Bot**, the **FastAPI Admin Backend**, and the **React Admin Dashboard**.

---

## 1. System Architecture Overview

The platform consists of four interconnected components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram User (Mobile / Desktop)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Telegram Bot API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Telegram Bot Engine (`app.main`)            │
│  - /start & 18+ Age Verification Gate                       │
│  - Category Browsing & Pagination                           │
│  - Curated Collections Browsing & Pagination                │
│  - Video Delivery (using Telegram file_id)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL Database (Local)                 │
│  - Users, Videos, Categories, Collections, Audit Logs       │
└──────────────────────────────▲──────────────────────────────┘
                               │ SQLAlchemy Async
                               │
┌──────────────────────────────┴──────────────────────────────┐
│             FastAPI Admin Backend (`app.api.main:app`)      │
│  - Port 8000 (REST API: /api/videos, /api/collections, etc.)│
│  - Video Upload Pipeline -> Telegram Storage Channel        │
│  - Admin Session Auth / Dev Mode                            │
└──────────────────────────────▲──────────────────────────────┘
                               │ HTTP / Proxy (Port 5173)
                               │
┌──────────────────────────────┴──────────────────────────────┐
│             React Admin Dashboard (`frontend/`)             │
│  - Vite + React + Tailwind Web Interface                    │
│  - Dashboard Stats, Video Uploader, Management, Collections │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

Ensure your host or WSL environment has the following installed:

| Tool | Minimum Version | Verification Command |
|---|---|---|
| **Linux / WSL** | Ubuntu 22.04+ | `lsb_release -a` |
| **Python** | 3.12+ | `python3 --version` |
| **PostgreSQL** | 14+ | `psql --version` |
| **Node.js & npm** | Node 18+, npm 9+ | `node -v && npm -v` |
| **Telegram Bot Token** | BotFather token | `123456789:ABCdefGhI...` |
| **Storage Channel** | Private Telegram Channel | e.g. `-1001234567890` |

---

## 3. Telegram Prerequisites (One-Time Setup)

### A. Create Your Bot via @BotFather
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the instructions to choose a name and username.
3. Save the **HTTP API token** provided (e.g., `7123456789:AAH...`).

### B. Create a Private Video Storage Channel
1. In Telegram, create a new **Private Channel** (e.g. `My Bot Storage`).
2. Add your newly created bot to this channel as an **Administrator** with full permissions (especially "Post Messages").
3. Get the Channel ID:
   - Forward any message from the channel to `@userinfobot` or `@JsonDumpBot`.
   - The ID starts with `-100` (e.g., `-1002345678901`).

---

## 4. Initial Installation & Configuration

### Step 1: Start PostgreSQL and Create Database
If PostgreSQL is not running:
```bash
sudo service postgresql start
```

Access `psql` and create the database:
```bash
sudo -u postgres psql
```

Inside the PostgreSQL shell:
```sql
CREATE DATABASE video_bot;
CREATE USER postgres WITH ENCRYPTED PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE video_bot TO postgres;
\q
```

---

### Step 2: Set Up Python Virtual Environment
Navigate to the project root:
```bash
cd /home/howtoquitvivek/tg-bot
```

Create and activate virtual environment (if not already created):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables (`.env`)
Create or edit your `.env` file in the project root:

```bash
cp .env.example .env
```

Open `.env` and fill in your actual credentials:
```env
# 1. Telegram Bot Token from @BotFather
BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 2. PostgreSQL async connection string
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/video_bot

# 3. Private Storage Channel ID (must start with -100)
TELEGRAM_STORAGE_CHANNEL_ID=-1002345678901

# 4. Authentication Mode
# Set to 'false' for local development (skips login prompts in web UI)
# Set to 'true' for production
AUTH_REQUIRED=false

# 5. Logging Level
LOG_LEVEL=INFO
```

---

### Step 4: Run Database Migrations
Apply all schema migrations using Alembic:
```bash
source .venv/bin/activate
alembic upgrade head
```

Verify migration status:
```bash
alembic current
```
You should see: `002_create_platform_models (head)`.

---

### Step 5: (Optional) Create Administrator Account
If you set `AUTH_REQUIRED=true`, create an admin user using the built-in CLI:
```bash
python -m app.cli create-admin --username admin --password your_secure_password
```

---

### Step 6: Configure Frontend & Firebase Authentication

The admin dashboard features a **Render Neo-Brutalist design language** with Google Popup Authentication and Firestore role-based access control.

1. **Navigate to the frontend folder and install dependencies:**
   ```bash
   cd /home/howtoquitvivek/tg-bot/frontend
   npm install
   ```

2. **(Optional / Recommended) Configure Firebase Authentication:**
   Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```

   In your [Firebase Console](https://console.firebase.google.com/):
   - Create a project (or select an existing one).
   - Go to **Authentication** > **Sign-in method** > enable **Google**.
   - Go to **Firestore Database** > create a database in production or test mode.
   - In Firestore, create a collection named `settings` and a document named `site`:
     ```json
     {
       "superAdminEmails": ["vivekbarman425@gmail.com"],
       "adminEmails": []
     }
     ```
   - Go to **Project Settings** > **General** > **Your apps** > create a Web app and copy the Firebase config into `frontend/.env`:
     ```env
     VITE_FIREBASE_API_KEY=AIzaSy...
     VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
     VITE_FIREBASE_PROJECT_ID=your-project
     VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
     VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
     VITE_FIREBASE_APP_ID=1:123456789:web:abcdef
     ```

   > [!NOTE]
   > **Local Dev Bypass:** If you do not configure Firebase credentials immediately, the gatekeeper screen detects this and provides a **"Bypass Authentication (Dev Mode)"** one-click button so you can test the dashboard locally without friction.

3. **Neo-Brutalist Themes:**
   The dashboard includes 7 custom high-contrast color palettes:
   - **Standard Pro** (`#48008C`)
   - **Midnight Noir** (`#0EA5E9`)
   - **Neon Cyber** (`#FF2079`)
   - **Forest Emerald** (`#064E3B`)
   - **Tokyo Night** (`#BB9AF7`)
   - **VS Dark Modern** (`#007ACC`)
   - **Slate Pro** (`#58A6FF`)

   You can switch themes anytime in the **Settings** tab. Your selection is automatically persisted in browser `localStorage`.

4. **Role Management:**
   - **SuperAdmin (`superAdminEmails`):** Access to all tabs + the **Admins** tab to add or remove administrator emails directly to/from Firestore.
   - **Admin (`adminEmails`):** Full access to Overview, Upload Video, Manage Videos, Categories, Collections, and Settings.

---

## 5. Running the Application (Development Mode)

### Option A: Single-Click Run Script (Recommended)

Run all three services (Telegram Bot, FastAPI Backend, and React Vite Dashboard) concurrently with a single command from the project root:

```bash
cd /home/howtoquitvivek/tg-bot
./run_dev.sh
# or shortcut:
./dev.sh
```

**What the script does automatically:**
- Verifies and connects to PostgreSQL.
- Runs pending Alembic database migrations.
- Installs missing frontend dependencies if needed.
- Frees any lingering zombie processes on ports 8000 and 5173.
- Launches **FastAPI** (`http://localhost:8000`), **Vite Frontend** (`http://localhost:5173`), and the **Telegram Bot polling engine**.
- Formats logs in real time with distinct color-coded prefixes (`[API]`, `[UI]`, `[BOT]`).
- Pressing `Ctrl+C` once cleanly terminates all services.

---

### Option B: Manual Multi-Terminal Execution

If you prefer running services in separate terminals:

### Terminal 1: Telegram Bot
Starts the aiogram polling engine:
```bash
cd /home/howtoquitvivek/tg-bot
source .venv/bin/activate
python -m app.main
```
*Expected output:*
```
[INFO] telegram_video_bot: Starting Telegram Video Bot (Bot: 712345...:***, DB: postgresql+asyncpg://postgres:***@localhost:5432/video_bot, LogLevel: INFO)
[INFO] telegram_video_bot: Database connection verified successfully.
[INFO] aiogram.dispatcher: Start polling
```

---

### Terminal 2: FastAPI Admin Backend
Runs the REST API server on `http://127.0.0.1:8000`:
```bash
cd /home/howtoquitvivek/tg-bot
source .venv/bin/activate
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected output:*
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### Terminal 3: React Admin Dashboard
Runs the Vite development server on `http://localhost:5173`:
```bash
cd /home/howtoquitvivek/tg-bot/frontend
npm run dev
```
*Expected output:*
```
  VITE v6.0.0  ready in 200 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 6. Accessing Platform Interfaces

| Interface | URL | Description |
|---|---|---|
| **Admin Web Dashboard** | [http://localhost:5173](http://localhost:5173) | Upload videos, manage categories & curated collections |
| **Interactive API Docs** | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Swagger UI for backend REST API |
| **Alternative API Docs** | [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc) | ReDoc API documentation |
| **API Health Check** | [http://localhost:8000/api/health](http://localhost:8000/api/health) | Returns `{"status":"ok","version":"0.2.0"}` |
| **Telegram Bot** | Your Telegram client | Search for your bot username and send `/start` |

---

## 7. Operational Workflow (End-to-End)

Follow these steps to test the entire system end-to-end:

### 1. Create a Category
1. Open the Admin Dashboard: `http://localhost:5173`.
2. Click **Categories** in the top navigation.
3. In the "Create New Category" form:
   - Name: `Highlights`
   - Description: `Best clips and previews`
4. Click **Create Category**.

### 2. Upload a Video
1. Click **Upload Video** in the top navigation.
2. Fill in the form:
   - **Video File:** Choose any `.mp4` video (up to 50 MB).
   - **Title:** `Demo Clip`
   - **Description:** `Sample video demonstration.`
   - **Category:** Select `Highlights`.
3. Click **Upload Video**.
4. The backend streams the video to your Telegram private storage channel, captures the Telegram `file_id`, and saves the video as `Draft`.

### 3. Publish the Video
1. Click **Manage Videos** in the top navigation.
2. Find `Demo Clip`. Notice its status is `DRAFT`.
3. Click **Publish**. The status changes to `PUBLISHED`.
*(Only published videos are visible to Telegram users).*

### 4. Create a Curated Collection
1. Click **Collections** in the top navigation.
2. Title: `Best of 2026`, Status: `Published`.
3. Click **Create Collection**.
4. Click **Manage & Videos** on the new collection card.
5. In the modal, select `Demo Clip` from the dropdown and click **Add Video**.
6. Click **Save Changes**.

### 5. View in Telegram Bot
1. In your Telegram app, start your bot: send `/start`.
2. If first time, tap **🔞 I am 18 or older**.
3. You will see the persistent main menu:
   - `Browse Videos`
   - `Collections`
   - `Help`
4. Tap **Browse Videos**:
   - The bot shows `📁 Highlights (1)`.
   - Tap `📁 Highlights` -> `🎬 Demo Clip`.
   - The bot streams and sends the video directly with rich caption and navigation buttons.
5. Tap **Collections**:
   - The bot shows `📚 Best of 2026 (1)`.
   - Tap to view and stream videos in collection order.

---

## 8. Running Automated Tests

Run the complete test suite (64 automated tests covering bot handlers, age gating, video delivery, collections, categories, and authentication):

```bash
cd /home/howtoquitvivek/tg-bot
source .venv/bin/activate
pytest -v
```

Python compilation sanity check:
```bash
python3 -m compileall app tests
```

Frontend production build check:
```bash
cd frontend
npm run build
```

---

## 9. Production Deployment Tips

When deploying to a remote server or VPS:

1. **Systemd Services:** Run the Telegram bot (`python -m app.main`) and the FastAPI backend (`uvicorn app.api.main:app`) as managed `systemd` daemon services so they restart automatically on server reboots.
2. **Reverse Proxy (Nginx / Caddy):**
   - Point your domain (e.g. `admin.yourdomain.com`) to Nginx.
   - Serve the production frontend static build (`frontend/dist`) directly via Nginx.
   - Proxy `/api` requests to `http://127.0.0.1:8000`.
3. **Security Settings in `.env`:**
   ```env
   AUTH_REQUIRED=true
   SECURE_COOKIES=true
   SECRET_KEY=generate-a-strong-random-64-char-string
   CORS_ORIGINS=["https://admin.yourdomain.com"]
   ```

---

## 10. Troubleshooting

| Symptom | Probable Cause | Fix |
|---|---|---|
| `Database connectivity check failed: [Errno 111] Connect call failed` | PostgreSQL service is stopped | Run `sudo service postgresql start`. |
| `Configuration validation failed: Field 'BOT_TOKEN'` | Token is missing or has placeholder text | Update `BOT_TOKEN` in `.env` with a real token from `@BotFather`. |
| `Upload failed: TelegramAPIError` | Bot is not admin in the storage channel | Ensure the bot is added to your private storage channel with administrator permissions to post messages. |
| `API Offline` badge in Dashboard | FastAPI backend is not running | Start the backend with `uvicorn app.api.main:app --port 8000`. |
| `No collections available` or `No videos` in Telegram | Content is still in `Draft` status | In the Admin Dashboard, publish the video or collection (`Draft` -> `Published`). |

