# Inkloom Guardian — AI-Powered Brand Governance & Content Trust Platform

## 1. Project Overview

**Inkloom Guardian** is an enterprise-grade full-stack brand governance and content trust platform. It enables marketing agencies to verify promotional text and visual media before publication against approved brand guidelines, validated source documents, registered claims, and prohibited terminology.

Unlike simplistic AI wrappers that hallucinate answers, **Inkloom Guardian is built on an evidence-first architecture**:
1. Every claim is checked against stored, client-specific database records.
2. AI-generated citations and quotations are strictly validated against stored source passages.
3. Every human approval or rejection is bound to an immutable content version snapshot.
4. Multi-client workspaces are strictly isolated at the database and query levels.

---

## 2. Complete Architecture

The platform is designed across four decoupled, high-assurance layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    1. PRESENTATION LAYER                    │
│      React 19 + Vite + Tailwind CSS v4 + Lucide Icons       │
│  - Dual-pane review interface (content left, findings right)│
│  - Workspace switcher, rule management & audit log views    │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON REST API / CORS
┌──────────────────────────────▼──────────────────────────────┐
│                 2. APPLICATION & API LAYER                  │
│               Python 3.14 + Django 6 + DRF                 │
│  - Authentication & Role-Based Access Control (RBAC)        │
│  - Multi-tenant workspace security filters                  │
│  - Immutable content versioning & workflow state transitions│
└──────────────────────────────┬──────────────────────────────┘
                               │ Django ORM
┌──────────────────────────────▼──────────────────────────────┐
│             3. DATABASE & PERSISTENCE LAYER                 │
│         PostgreSQL (Production) / SQLite (Local Dev)        │
│  - 17 core relational models                                │
│  - Foreign key constraints, version snapshots, audit logs   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│           4. AI & EVIDENCE VERIFICATION ENGINE              │
│  - Stage A: Normalisation & positional sentence splitting    │
│  - Stage B: Deterministic regex brand rule & term checks     │
│  - Stage C: Client-isolated source evidence retrieval       │
│  - Stage D: Structured grounded AI analysis                 │
│  - Stage E: Source ID & citation quotation validation        │
│  - Stage F: Status assignment (SUPPORTED, CONTRADICTED...)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```text
inkloom web/
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration (git-ignored)
├── .gitignore                # Git ignore rules for Python, Node, media, DB
├── README.md                 # Master project documentation & guide
├── venv/                     # Python 3.14 virtual environment
├── backend/                  # Django REST API Backend
│   ├── manage.py             # Django management CLI
│   ├── requirements.txt      # Python dependencies
│   ├── db.sqlite3            # Local development database
│   └── inkloom_backend/      # Project settings & root routing
│       ├── __init__.py
│       ├── settings.py       # DRF, CORS, Auth, Database configuration
│       ├── urls.py           # Top-level API routing & health check
│       ├── wsgi.py
│       └── asgi.py
└── frontend/                 # React + Vite Frontend
    ├── package.json          # Node dependencies & build scripts
    ├── vite.config.js        # Vite config with Tailwind & API proxy
    ├── index.html            # Entry HTML
    └── src/
        ├── App.jsx           # Main application view & status dashboard
        ├── App.css           # Custom CSS rules
        ├── index.css         # Tailwind CSS & design tokens
        └── main.jsx          # React DOM entry point
```

---

## 4. Layer Responsibilities

| Layer | Responsibility | Key Technologies |
| :--- | :--- | :--- |
| **Frontend** | Renders responsive UI, captures user input, provides interactive review interface, side-by-side claim diffs, visual feedback. | React 19, Vite 8, Tailwind CSS v4, Lucide React |
| **Backend API** | Enforces business rules, authentication, permissions per workspace, validates data, runs verification pipelines, generates immutable snapshots. | Django 6, Django REST Framework, django-cors-headers |
| **Database** | Stores organisations, client workspaces, memberships, rules, claims, sources, content items, immutable versions, findings, approvals, and audit events. | PostgreSQL / SQLite, Django ORM |
| **Evidence & AI Layer** | Pre-processes text, executes deterministic checks, retrieves evidence within the active workspace, invokes AI providers with structured output, verifies citations. | Python regex, Provider Adapters (Gemini / OpenAI / Anthropic / Mock) |

---

## 5. Prerequisites & Local Installation

### Prerequisites
- Python 3.11+ (Python 3.14 supported)
- Node.js 18+ (Node.js 24 supported) & npm 10+
- Git

### Quick Setup

1. **Activate Virtual Environment & Install Backend Dependencies**:
   ```bash
   # From the project root:
   .\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   cd backend
   python manage.py migrate
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd ../frontend
   npm install
   ```

4. **Running Both Servers**:
   - **Fastest workflow (single command)**:
     ```bash
     cd frontend
     npm run dev:all
     ```
     This starts the Django API and the Vite frontend together in one terminal session.
   - **Manual split workflow**:
     - **Terminal 1 (Backend)**:
       ```bash
       cd backend
       ..\venv\Scripts\python.exe manage.py runserver 8000
       ```
     - **Terminal 2 (Frontend)**:
       ```bash
       cd frontend
       npm run dev
       ```
   - **VS Code backend debugging**:
     - Open **Run and Debug** and select **Django: Run backend**.
     - This configuration uses the workspace `venv` interpreter; press **F5** to start the API.
     - Start the frontend separately with `npm run dev` from the `frontend` directory.
   - Open browser at `http://localhost:5173`.
   - The frontend automatically proxies `/api/*` requests to `http://127.0.0.1:8000`.
