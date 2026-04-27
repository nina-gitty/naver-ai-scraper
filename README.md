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

## 🛡️ Privacy & Security Note

For your privacy, the following files are **excluded from the repository** via `.gitignore`:
- `backend/user_data/`: Contains browser profile data, cookies, and cache.
- `backend/static/screenshots/*.png`: Local copies of collected search results.
- `backend/quota.json`: Your local daily usage history.

*Note: The first time you run a scan, Naver might challenge the automation. You can set `headless=False` in `backend/main.py` once, perform a manual search or login, and then revert it to `True` to build trust for the session.*

---

## 📄 License
This project is for private/internal monitoring purposes.
