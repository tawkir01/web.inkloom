# Inkloom Guardian — AI-Powered Brand Governance & Content Trust Platform

## 1. Project Overview

**Inkloom Guardian** is an enterprise-grade full-stack brand governance and content trust platform. It enables marketing agencies to verify promotional text and visual media before publication against approved brand guidelines, validated source documents, registered claims, and prohibited terminology.

**Inkloom Guardian currently runs deterministic brand-rule checks and conservative, evidence-linked claim checks**:
1. Checks use stored, client-specific rules, approved claims, and source passages.
2. Any source quotation returned by the deterministic engine comes from a stored source record.
3. Every human approval or rejection is bound to an immutable content version snapshot.
4. Multi-client workspaces are strictly isolated at the database and query levels.

AI analysis is optional. With `AI_PROVIDER=mock` or no API key, reviews run deterministic checks only. When configured for `openai`, `anthropic`, or `gemini`, the backend can send submitted text and current workspace-approved claims and source passages to that provider. Provider usage can incur charges. The deterministic layer remains independent, and a provider failure is reported separately without hiding successful deterministic results. Word overlap is not treated as proof that a claim is supported; the pipeline returns `UNABLE_TO_DETERMINE` when source wording only overlaps without an exact passage match.

### Evidence-linked claim review

1. Register a source document in the selected client workspace and add an approved, currently valid version with its evidence passages.
2. Register the approved claim and link it to the supporting source version.
3. Submit copy and run a governance review. Claim findings include the source document code, title, version, and a stored passage; they explain the issue and suggest the approved wording or required qualifier.
4. Revise the copy and run the review again on the new content version before requesting approval.

Brand rules, claims, source documents, and content history are scoped to the selected workspace. Source versions are append-only in the application and cannot be deleted while preserving an audit trail. Each finding stores the exact source document code, title, and version label used at review time, alongside its cited passage; later document metadata changes do not rewrite previous findings.

Source links are optional for older claims. When no current source version is linked, findings cite the approved claim statement instead of presenting an unverified document passage as evidence.

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
│          4. OPTIONAL AI & EVIDENCE VERIFICATION              │
│  - Stage A: Normalisation & positional sentence splitting    │
│  - Stage B: Deterministic regex brand rule & term checks     │
│  - Stage C: Client-isolated source evidence retrieval       │
│  - Stage D: Conservative source-text comparison              │
│  - Stage E: Source ID & quotation validation                 │
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
| **Evidence layer** | Executes deterministic checks, retrieves workspace-scoped evidence, and avoids treating lexical overlap as proof. | Python regex, Django ORM |

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
   python manage.py seed_demo_data
   ```
   The seed command creates the fictional demo role accounts, workspaces, and a sample EcoVolt review item. It is safe to run again to restore demo data.

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
   - Open browser at `http://localhost:5173/stackinkloom/`.
   - The frontend automatically proxies `/api/*` requests to `http://127.0.0.1:8000`.

### Demo role access

The login screen's demo role cards sign in directly. Each role uses the same workspace interface, with actions shown according to its permissions:
- **Content Creator** and **Agency Admin** can submit content and create revisions.
- **Brand Reviewer** and **Agency Admin** can record approval decisions.
- **Account Manager** can follow the shared review queue and add coordination comments, but cannot submit or approve content.

## Environment and production deployment

Copy `.env.example` to `.env` for local development. In production, supply environment variables through the backend host rather than committing a `.env` file:

- Set `DEBUG=False`, a unique strong `SECRET_KEY`, and `ALLOWED_HOSTS` to the backend hostnames.
- Set `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to the actual frontend origin(s). Do not use wildcard origins with credentials.
- Keep HTTPS enabled. `SECURE_SSL_REDIRECT`, secure cookies, and HSTS default on when `DEBUG=False`; only set `USE_X_FORWARDED_PROTO=True` when the trusted hosting proxy sets that header.
- Configure database connection variables on the backend host if using PostgreSQL. Never put database credentials or AI keys in `frontend/` or a `VITE_*` variable.
- `VITE_API_BASE_URL` is a public frontend build-time setting for the backend origin. The existing GitHub Pages base path remains `/stackinkloom/`.
- `AI_PROVIDER`, `AI_API_KEY`, and `AI_MODEL_NAME` configure optional backend analysis. Supported provider identifiers are `mock`, `openai`, `anthropic`, and `gemini`; use `mock` when no provider call should be made. The OCR setting remains reserved; no OCR adapter is currently configured.
- Keep `AI_API_KEY` on the backend host only. Live reviews send submitted copy and the active workspace's approved claims and valid evidence passages to the selected provider; review each provider's data-retention and pricing terms before enabling it.

Apply migrations before starting a backend release:

```bash
cd backend
python manage.py migrate
```

Run backend validation from `backend/` with `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`. Run frontend validation from `frontend/` with `npm run build` and `npm run lint`.
