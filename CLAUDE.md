# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**imputaciones-powersap** is a full-stack app that manages time imputations (imputaciones) from PowerApps and adapts them to SAP format for Division 3. Service name: `powersap`.

## Development Commands

### Docker (primary development method)

```bash
# Start all services (dev mode with hot-reload)
docker-compose up --build

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Dev mode auto-runs `alembic upgrade head` before starting the backend.

### Frontend (inside container or local)

```bash
cd frontend
npm install
npm run dev          # Vite dev server
npm run build        # Production build
npm test             # Run vitest
```

### Backend

```bash
cd backend
pip install -r requirements.txt
pytest               # Run tests
```

### Database Migrations

```bash
cd backend
alembic upgrade head           # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

## Architecture

### Stack

- **Backend**: FastAPI (Python 3.11) + SQLAlchemy 2.0 + Alembic + PostgreSQL 15
- **Frontend**: React 18 + MUI 6 + Vite 4 + React Router 7 + Axios
- **Deployment**: Docker Compose, Nginx (prod), Traefik reverse proxy (prod)

### Backend Structure (`backend/app/`)

- `main.py` — FastAPI app entry point, CORS config, router registrations
- `api/routes/` — one router file per feature (agregar_imputaciones, generar_imputaciones_sap, etc.)
- `services/` — business logic, organized by domain in subdirectories
- `models/models.py` — all SQLAlchemy ORM models in one file
- `core/config.py` — database config from environment variables
- `core/sse_manager.py` — global SSEManager singleton for real-time progress streaming
- `db/session.py` — SQLAlchemy engine and session factory

**Key pattern — SSE-driven long processes:**
Most operations follow a 3-step flow:
1. `POST /start` — kicks off a background task, returns a `process_id`
2. `GET /events/{process_id}` — SSE stream for real-time log/progress messages
3. `GET /download/{process_id}` — retrieve the result file (ZIP/CSV/XLSX)

### Frontend Structure (`frontend/src/`)

- `routes/routesAuto.jsx` — auto-discovers pages via `import.meta.glob('../pages/*.jsx')`; each page exports a `meta` object with `label` and `priority`
- `pages/` — one file per page/view
- `hooks/` — one custom hook per feature (e.g., `useAgregarImputaciones`), keeps page components clean
- `services/` — API call functions per feature (one file each)
- `hooks/useSSE.js` — generic SSE consumer hook used across features
- `contexts/` — `ThemeContext` (light/dark) and `PageContext` (active page tracking)
- `theme/index.js` — MUI light/dark theme definitions

### API Base Path

All API routes are under `/{SERVICE_NAME}/api` (i.e., `/powersap/api`). The frontend `BrowserRouter` uses `VITE_SERVICE_NAME` as basename.

### Business Logic Flow

1. **Agregar Imputaciones** — upload PowerApps Excel → `Imputaciones` table
2. **Cargar Tareas SAP** — upload SAP operations Excel → `Sap_Orders` table
3. **Generar Imputaciones SAP** — matching algorithm assigns SAP orders to imputaciones, writes to `Tabla_Central`, outputs ZIP with CSV+XLSX
4. **Cargar Respuesta SAP** — upload SAP's response file to mark rows as loaded
5. **Obtener Feedback** — review results and failures

### Matching Algorithm (Generar Imputaciones SAP)

For each pending imputación:
1. **GG match** — if TipoIndirecto + TipoMotivo exist, match via Areas.OpGG
2. **Resolve operation** — from extraciclos (if TareaAsoc) or from Tarea
3. **Translate project** — BAAN → SAP via Projects_Dictionary
4. **Exact match** — find SapOrder with matching project + vértice + coche + OperationActivity
5. **No match → DISCARD** — imputaciones without exact match are not inserted into Tabla_Central

### Feedback States

| State | Color | Meaning |
|---|---|---|
| `0 - No admitida` | Red (C00000) | Not found in DB or no Tabla_Central entry |
| `1 - Cargado en SAP` | Green (00B050) | Successfully loaded in SAP |
| `2 - Pendiente de carga en SAP` | Amber (FFC000) | In Tabla_Central but not yet loaded |

### Important: Leading Zeros

All Excel reads use `dtype=str` to preserve leading zeros in project codes (e.g., `"0512"` stays `"0512"`, not `512`). Numeric fields (Horas, CarNumber, ProductionOrder) are explicitly converted after reading.

### Key Database Tables

- `Imputaciones` — time entries from PowerApps
- `Sap_Orders` — SAP work orders
- `Tabla_Central` — pivot table linking imputaciones to SAP orders
- `Projects_Dictionary` — Baan-to-SAP project code mapping
- `Areas` — work center to area mappings
- `Extraciclos` — extra-cycle area/task mappings

## Environment

Single `.env` file at project root consumed by Docker Compose. Backend reads via `os.getenv()` with fallback defaults. Frontend reads `VITE_*` vars injected at build time.

## Debugging

VS Code compound debug config in `.vscode/launch.json` attaches to both backend (`debugpy` on port 5678) and frontend (Chrome DevTools).
