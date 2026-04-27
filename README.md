# Naver AI Briefing Insights

A professional-grade monitoring tool to track and analyze **Naver AI Briefing** (Generative AI summary) exposure in real-time. Built with FastAPI, Playwright, and React.

## 🚀 Key Features

- **Advanced Bot Evasion**: Uses `playwright-stealth` and **Persistent Browser Context** to mimic real human behavior and bypass sophisticated bot detection.
- **Hybrid Incognito-Persistent Mode**: Maintains a trusted browser fingerprint while clearing cookies on each run to ensure unbiased, generic AI results.
- **Real-time Monitoring**: Live progress tracking with **ETA calculation** and dynamic keyword counting.
- **Safe Guard Quota System**: Daily usage tracking with persistent storage (`quota.json`) to prevent IP bans.
- **Dynamic UI**: Responsive dashboard with localized (English) interface and automatic screenshot management.
- **Data Export**: One-click CSV export categorized by source locations (Carousel, Panel).

## 🛠️ Tech Stack

- **Frontend**: React, Vite, Lucide-React, CSS3
- **Backend**: Python, FastAPI, Playwright, sse-starlette
- **Automation**: Playwright Stealth

---

## 🏁 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **npm** or **yarn**

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser engine
playwright install chromium
```

### 2. Frontend Setup (React/Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

---

## 🏃 Running the Application

### Start Backend Server
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

The application will be available at **http://localhost:5173**.

---

## 🛡️ Session Initialization (Building Trust)

To effectively bypass Naver's bot detection, you must "train" your local browser session. The `user_data` folder stores your unique browser fingerprint, making you look like a real human user.

### How to Generate & Initialize `user_data`

1. **Enable Headed Mode**: Open `backend/main.py` and change `headless=True` to `headless=False` (around line 155).
2. **Run a Task**: Start the backend and frontend, then run a simple search for 1-2 keywords.
3. **Manual Interaction**: When the browser window pops up, **manually perform a search** on Naver or **log in** with a dummy account. This generates the necessary cookies and history in `backend/user_data/`.
4. **Re-enable Stealth**: Once successful, change `headless` back to `True`.

### Where is it stored?
- **Path**: `backend/user_data/`
- This folder is unique to your machine and is **ignored by Git** for your security.

---

## 🛡️ Privacy & Security Note

For your privacy, the following files are **excluded from the repository** via `.gitignore`:
- `backend/user_data/`: Contains browser profile data, cookies, and cache.
- `backend/static/screenshots/*.png`: Local copies of collected search results.
- `backend/quota.json`: Your local daily usage history.

*Note: The first time you run a scan, Naver might challenge the automation. You can set `headless=False` in `backend/main.py` once, perform a manual search or login, and then revert it to `True` to build trust for the session.*

---

## 📄 License
This project is for private/internal monitoring purposes.
