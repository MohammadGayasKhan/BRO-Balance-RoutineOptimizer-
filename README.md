# RythMind Cognition

A conversational AI assistant that connects to your **Google Calendar** to analyse working hours, suggest relaxation, show upcoming work, and find free time — powered by **Grok** (xAI).

## Architecture

```
RythMindCognition/
├── backend/              ← FastAPI (Python)
│   ├── main.py           ← Entry point
│   ├── app/
│   │   ├── config.py     ← Environment settings
│   │   ├── api/          ← Route handlers
│   │   │   ├── auth.py       Google OAuth flow
│   │   │   ├── calendar.py   Event CRUD
│   │   │   ├── chat.py       Grok AI chat
│   │   │   └── analytics.py  Working-hours analytics
│   │   ├── services/     ← Business logic
│   │   │   ├── google_calendar.py
│   │   │   ├── grok_ai.py
│   │   │   └── vector_db.py   (optional Pinecone KB)
│   │   └── models/
│   │       └── schemas.py     Pydantic models
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/             ← Angular 19
│   ├── src/app/
│   │   ├── core/         ← Services, guards, interceptors
│   │   ├── features/     ← Page components
│   │   │   ├── auth/         Login & OAuth callback
│   │   │   ├── dashboard/    Home dashboard
│   │   │   ├── calendar/     Event list & create
│   │   │   ├── chat/         BRO chat interface
│   │   │   └── analytics/    Working-hours charts
│   │   └── shared/       ← Models, navbar
│   ├── package.json
│   └── proxy.conf.json   ← Dev proxy → localhost:8000
```

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → add your GROK_API_KEY (and optionally PINECONE_API_KEY)

# Place your Google OAuth credentials.json in backend/
# (Download from Google Cloud Console → APIs & Services → Credentials)

# Run
uvicorn main:app --reload
```

The API starts at **http://localhost:8000**. Swagger docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Angular dev server starts at **http://localhost:4200** and proxies `/api` to the backend.

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project → enable **Google Calendar API**.
3. Create **OAuth 2.0 Client ID** (Web application).
4. Add redirect URI: `http://localhost:8000/api/auth/callback`.
5. Download `credentials.json` → place in `backend/`.

### 4. Grok API Key

1. Get your API key from [xAI Console](https://console.x.ai/).
2. Add to `backend/.env` as `GROK_API_KEY=xai-...`.

## Features

| Feature | Description |
|---------|-------------|
| **Chat with BRO** | Conversational AI that knows your calendar – ask about schedule, workload, free time |
| **Working Hours Analytics** | 30-day breakdown of work vs leisure, stress level, freedom score |
| **Event Management** | Create and delete Google Calendar events |
| **Vector Knowledge Base** | Optional Pinecone integration for semantic event search |

## Tech Stack

- **Backend**: FastAPI, Google Calendar API, OpenAI-compatible Grok client
- **Frontend**: Angular 19 (standalone components, signals, lazy-loaded routes)
- **AI**: Grok (xAI) via OpenAI-compatible API
- **Vector DB**: Pinecone + SentenceTransformers (optional)
