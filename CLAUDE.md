# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A one-stop material management system (一站式物资管理系统) for campus use — warehousing, storage, requisition, and recycling. Vue 3 + Vite frontend with a FastAPI + SQLAlchemy backend.

## Development Commands

```bash
# Frontend (from project root)
npm install                # Install frontend dependencies
npm run dev                # Start Vite dev server (http://localhost:5173)
npm run build              # Production build
npm run preview            # Preview production build

# Backend (from backend/)
cd backend
pip install -r requirements.txt    # Install Python dependencies
uvicorn main:app --reload          # Start API server (http://localhost:8000)

# Docker (from project root, requires Docker)
docker-compose up --build          # Start backend + PostgreSQL
```

The frontend dev server proxies `/api` requests to `localhost:8000` via `vite.config.js`. You need both servers running (or just Docker for a full stack).

API docs are at `http://localhost:8000/docs` (Swagger).

**Testing APIs without a running server:**
```python
from main import app
from fastapi.testclient import TestClient
c = TestClient(app)
r = c.get("/api/health")
print(r.json())
```

## Architecture

### Frontend (Vue 3 + Vite)

- **No Vue Router** — all navigation is via modal visibility state and `currentView` ref in `App.vue`. Supported views: `'all'` (default card grid), `'warehouse'` (warehouse dashboard), `'detail'` (single warehouse drill-down), `'reports'` (restock report page).
- **No Pinia** — a single centralized store (`src/store/useStore.js`) built on `reactive()` + `computed()`, Service Locator pattern via `useStore()`
- **All components use `<script setup>`** Composition API
- **CSS**: Glassmorphism design, no UI framework. CSS custom properties and utility classes in `src/style.css`, scoped styles in each component.
- **Modals**: All modals use `<Teleport to="body">` + `.modal-overlay` + scale-animated `.modal-content` + `watch(visible)` to reset form state on open. Consistent `defineProps({visible: Boolean})` / `defineEmits(['close', 'done'])` pattern.

### Backend (FastAPI + SQLAlchemy)

- **Database**: SQLite by default at `backend/data/inventory.db`. Set `DATABASE_URL` env var to use PostgreSQL instead — `database.py` auto-detects and adjusts driver options.
- **Engine**: SQLAlchemy 2.0 ORM with `declarative_base()`, sessions via `get_db()` dependency
- **Seeding**: `backend/seed.py` runs on startup, idempotent (skips if data exists). Admin password defaults to `admin888` but can be overridden via `ADMIN_PASSWORD` env var.
- **Lifespan**: `main.py` creates tables then seeds on startup via `@asynccontextmanager`
- **CORS**: Fully open origins (`allow_origins=["*"]`), `allow_credentials=False`
- **Security**: Admin password stored as SHA-256 + random salt hash (`hash:salt` format). `GET /api/admin/settings` filters out `password` and `smtp_pass`. Excel upload capped at 10 MB. Backward compatible with plaintext passwords from older databases.

### API Response Convention

Every endpoint returns `{"ok": bool, "data": ..., "msg": "..."}`. Frontend `api/client.js` wraps all requests to return this shape, catching network errors as `{ok: false, msg: "网络错误: ..."}`.

### Data Flow

```
User click → App.vue handler → store action → api/*.js → FastAPI endpoint → service → SQLAlchemy → SQLite
                                                     ← JSON response ←
App.vue handler → store.loadAll() → DOM updates via reactive bindings
```

### Field Name Conventions

**Backend → Frontend**: API returns `snake_case` (e.g., `has_individual_tracking`, `material_id`, `created_at`). The store in `loadMaterials()` maps a few fields to camelCase aliases: `totalQuantity` ← `total_quantity`, `borrowedQuantity` ← `borrowed_quantity`. All other fields are accessed in their original snake_case form in templates and components. Always check the actual API response before using a field in a component — snake_case is the default.

### Global Toast

`src/utils/toast.js` provides a singleton `toast(msg, type)` function. Import in any component via `import { toast } from '../utils/toast.js'`. Types: `'success'`, `'error'`, `'info'`, `'warning'`. Never use bare `alert()` for error feedback.

### Two Inventory Models

| Model | Table | When Used | Key Field |
|-------|-------|-----------|-----------|
| `InventoryBatch` | `inventory_batches` | Bulk consumables (water, tissues, pens) | `quantity: int` |
| `InventoryItem` | `inventory_items` | Individually-tracked items (AC remotes) | `code: str`, `status: available/borrowed` |

A material's `has_individual_tracking` flag determines which model is used. Mutually exclusive — a material uses one or the other.

### Warehouse + Sub-Category System

Three warehouse roles via material `sub_category`:

| `sub_category` | Borrow Behavior | Transfer Eligible |
|---|---|---|
| `direct_consumption` | Deduct from main warehouse only | No |
| `new_consumable` | Deduct from main warehouse only | No |
| `recyclable` | **Recycling warehouse first**, then main | Yes |

Two physical warehouses created by seed: "主仓库" (main) and "回收仓" (recycling). Transfer API (`POST /api/transfer`) moves recyclable items from main to recycling warehouse.

### Key Files

| File | Role |
|---|---|
| `src/App.vue` | Root component — all modals, view switching logic, event orchestration |
| `src/store/useStore.js` | All state, getters, loaders, actions |
| `src/utils/toast.js` | Global toast notification singleton — `toast(msg, type)` |
| `src/api/client.js` | HTTP client — `apiGet/apiPost/apiPut/apiDelete/apiUpload` |
| `backend/main.py` | App factory, lifespan, router registration |
| `backend/models.py` | 7 SQLAlchemy ORM models with indexes on FK/status/date columns, unique constraint on Material.name |
| `backend/schemas.py` | All Pydantic request/response schemas |
| `backend/services/inventory_service.py` | Borrow/return/transfer business logic with priority rules |
| `backend/services/import_service.py` | Excel import via openpyxl |
| `backend/services/report_service.py` | Consumption velocity, stockout prediction, trend analysis |
| `backend/services/email_service.py` | SMTP email with HTML report template |
| `backend/routers/*.py` | 8 route modules (materials, warehouses, inventory, borrow, transfer, import_, admin, reports) |

### Seed Data on Startup

- **2 warehouses**: 主仓库 (一楼库房), 回收仓 (书画室旁)
- **4 materials**: 空调遥控器 (durable/recyclable, 20 tracked items), 饮用水 (direct_consumption, 50桶/已借12), 纸巾 (direct_consumption, 100包/已借30), 笔 (recyclable, 60支/已借18, 其中回收仓5支)
- **Admin password**: `admin888` (stored as SHA-256 hash, plaintext `admin888` in old databases auto-upgraded on first login)

### Reset Database

Delete `backend/data/inventory.db` and restart the server. The seed script will recreate it.

## Phase 2 Features (Completed)

- **Multi-warehouse view**: Click 🏗️ in header → warehouse dashboard with stats cards → click into warehouse detail (materials tab + locations tab)
- **Inbound workflow**: `POST /api/inbound` — formal inbound with warehouse + location selection, preview confirmation
- **Warehouse transfer**: `POST /api/transfer` — move recyclable items between warehouses, quantity sync
- **Borrow priority**: Recyclable items automatically deduct from recycling warehouse first
- **Per-warehouse stats**: `GET /api/warehouses/stats` — material count, total quantity, low stock alerts per warehouse
- **Warehouse detail**: `GET /api/warehouses/{id}/detail` — materials + locations per warehouse
- **Material breakdown**: `GET /api/materials/{id}/warehouse-breakdown` — shows quantity per warehouse

## Phase 3 Features (Completed)

### Cloud Database Support
- **PostgreSQL optional**: Set `DATABASE_URL` env var to switch from SQLite (default) to PostgreSQL. `database.py` auto-detects and adjusts connect args.
- **Docker**: `Dockerfile`, `docker-compose.yml` (backend + PostgreSQL 16), `.dockerignore` provided. `docker-compose up` brings up both services.
- **Environment config**: `.env.example` with all settings. `python-dotenv` loads `.env` on startup. Admin password can be set via `ADMIN_PASSWORD` env var.

### Dynamic Inventory Alerts
- **Consumption velocity**: `services/report_service.py` — calculates daily consumption rate from BorrowHistory (borrow - return over N days).
- **Stockout prediction**: Days until stockout = current stock / daily rate. Status: critical (≤7 days), warning (≤30 days), ok (>30), insufficient_data.
- **API endpoints**: `GET /api/reports/dashboard-alerts`, `GET /api/reports/restock-suggestions`, `GET /api/reports/consumption-trends`, `GET /api/reports/material-alert/{id}`, `GET /api/reports/export`

### Reports Page
- **ReportsPage.vue**: Full-page view with summary cards (critical/warning/data-insufficient/total), sortable table, expandable consumption trend bar charts, Excel export, period selector (30/60/90 days).
- **AlertBanner.vue**: Amber warning banner on main dashboard when items are low, with animated pulse icon and link to reports.
- **AppHeader**: Reports button (📊) with red badge showing alert count.

### Email Notifications
- **SMTP configuration**: In AdminPanel — host, port, user, auth code, from/to email fields. Test email button to verify. Settings stored in AdminSetting key-value table.
- **Email service**: `services/email_service.py` — generates HTML report email (restock table + summary cards) and sends via SMTP.
- **API**: `POST /api/reports/send-email`, `GET /api/reports/email-status`, `POST /api/admin/test-email`, `GET /api/admin/settings`, `PUT /api/admin/settings`
- **Schedule**: Manual trigger from ReportsPage. Cron/Task Scheduler can automate: `curl -X POST http://localhost:8000/api/reports/send-email`

### Key New Files
| File | Role |
|---|---|
| `backend/services/report_service.py` | Consumption velocity, stockout prediction, trend analysis |
| `backend/services/email_service.py` | SMTP email sending with HTML report template |
| `backend/routers/reports.py` | 7 report + email endpoints |
| `src/api/reports.js` | Frontend API client for reports |
| `src/components/ReportsPage.vue` | Full report page with charts and export |
| `src/components/AlertBanner.vue` | Dashboard warning banner |

## Phase 4 (Not Yet Implemented)

See `README.md`. Remaining: barcode scanner integration, simplified terminal UI for scanner workflows.
