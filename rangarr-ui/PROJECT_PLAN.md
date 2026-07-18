# Rangarr UI - Project Plan

A modern, responsive admin dashboard for Rangarr orchestration service. Built as a companion project that communicates with rangarr via a minimal REST API.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technical Stack](#technical-stack)
4. [API Contract](#api-contract)
5. [Feature Requirements](#feature-requirements)
6. [Implementation Tasks](#implementation-tasks)
7. [Design Specifications](#design-specifications)
8. [Deployment](#deployment)

---

## Project Overview

**Purpose:** Provide a web-based admin interface for monitoring, controlling, and analyzing Rangarr search orchestration.

**Scope:**
- Real-time system status and metrics
- Per-instance visibility (queue depth, last search, success rates)
- Search history and trending data
- Manual search triggering (optional)
- Configuration validation/dry-run testing
- Live log streaming and filtering

**Non-Scope (v1):**
- Configuration editing (read-only)
- User authentication/multi-user
- Database persistence
- External integrations (Slack, Discord, etc.)
- Mobile app

**Philosophy:** Keep it lightweight, optional, and easy to self-host. Dashboard should never break rangarr's auditability or add security risk to core.

---

## Architecture

### High-Level Flow

```
Rangarr (Core)
├─ Orchestration loop (unchanged)
├─ REST API endpoints (NEW: minimal)
└─ Structured JSON logging (NEW: log sink)
                ↓
Rangarr API (FastAPI, ~200 lines)
├─ GET /api/status
├─ GET /api/config
├─ GET /api/logs
├─ GET /api/instances
├─ GET /api/metrics
└─ POST /api/search/trigger (optional)
                ↓
Rangarr UI (React frontend)
├─ Real-time polling/WebSocket
├─ Dashboard pages
├─ Charts & visualizations
└─ Live log viewer
                ↓
Browser (User)
```

### Component Diagram

```
rangarr-ui/
├── backend/                    # Optional thin proxy/cache layer
│   ├── api/                    # API abstraction
│   ├── services/               # Business logic (optional)
│   └── cache.py                # In-memory cache (optional)
│
├── frontend/                   # React SPA
│   ├── pages/
│   │   ├── Dashboard.tsx       # Home page (status, live metrics)
│   │   ├── Instances.tsx       # Per-instance details
│   │   ├── Logs.tsx            # Log viewer & search
│   │   ├── Metrics.tsx         # Historical charts
│   │   └── Config.tsx          # Configuration viewer
│   ├── components/
│   │   ├── StatusCard.tsx
│   │   ├── InstanceTable.tsx
│   │   ├── LogViewer.tsx
│   │   ├── SearchHistory.tsx
│   │   ├── Charts.tsx
│   │   └── Header.tsx
│   ├── hooks/
│   │   ├── useRangarrAPI.ts    # API calls + polling
│   │   ├── useWebSocket.ts     # Real-time log streaming (optional)
│   │   └── useMetrics.ts       # Data transformation
│   ├── styles/
│   │   ├── theme.ts            # *arr dark theme
│   │   └── global.css
│   └── App.tsx
│
├── docker/
│   ├── Dockerfile
│   └── nginx.conf              # Reverse proxy (optional)
│
├── public/
│   └── index.html
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## Technical Stack

### Frontend

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **Framework** | React 18+ with TypeScript | Modern, widely-used, matches *arr ecosystem |
| **Build Tool** | Vite | Fast HMR, optimized bundle, minimal config |
| **State Management** | TanStack Query (React Query) + Zustand | Real-time data + simple app state |
| **Charts** | Recharts or Chart.js | Lightweight, React-friendly, good *arr aesthetic fit |
| **UI Components** | shadcn/ui or Headless UI + Tailwind | Accessible, themeable, minimal bundle |
| **Styling** | Tailwind CSS | Utility-first, fast iteration, dark mode native |
| **HTTP Client** | Axios | Simple, cancellable requests, global interceptors |
| **Icons** | Lucide React or React Icons | Lightweight, SVG-based |
| **Real-Time** | WebSocket via native API (optional) | For live log streaming |

### Backend (Optional Thin Layer)

| Component | Specification | Notes |
|-----------|---------------|-------|
| **Language** | Python | Consistency with rangarr |
| **Framework** | FastAPI (lightweight) | Async, validation, OpenAPI docs |
| **Purpose** | Cache + proxy (optional) | Deduplicates API calls, smooths polling |
| **Deployment** | Same Docker container as UI or separate | Keep simple |

### DevOps & Testing

| Component | Specification |
|-----------|---------------|
| **Container** | Node 20+ alpine (frontend) or Python 3.13 (backend) |
| **Reverse Proxy** | Nginx (included in image) |
| **Env Vars** | `RANGARR_API_URL`, `POLL_INTERVAL_MS`, `THEME_MODE` |
| **API Testing** | Postman Collection (v2.1 JSON format) |
| **Documentation** | OpenAPI/Swagger spec (auto-generated from FastAPI) |

---

## API Contract

### Rangarr Core → API Layer

These endpoints must be added to rangarr's `api.py` (FastAPI). All endpoints return JSON and are read-only (except POST /search/trigger).

#### 1. `GET /api/status`
**Purpose:** Current rangarr state and cycle info

**Response:**
```json
{
  "running": true,
  "uptime_seconds": 86400,
  "current_cycle": 342,
  "next_missing_in_seconds": 1234,
  "next_upgrade_in_seconds": 2345,
  "last_cycle_duration_ms": 127,
  "total_searches_triggered": 5230,
  "dry_run_mode": false,
  "active_hours_active": true,
  "timestamp": "2026-07-18T14:23:45Z"
}
```

#### 2. `GET /api/config`
**Purpose:** Current configuration (secrets redacted)

**Response:**
```json
{
  "global": {
    "interval_minutes": 60,
    "interval_missing_minutes": 30,
    "interval_upgrade_minutes": 120,
    "missing_batch_size": 20,
    "upgrade_batch_size": 10,
    "stagger_interval_seconds": 30,
    "search_order": "last_searched_ascending",
    "active_hours": "22:00-06:00",
    "dry_run": false,
    "interleave_instances": false,
    "interleave_types": true,
    "retry_interval_days": 30,
    "max_queue_size": 0,
    "season_packs": false
  },
  "instances": [
    {
      "name": "Radarr-Movies",
      "type": "radarr",
      "host": "http://radarr:7878",
      "enabled": true,
      "weight": 1.5,
      "max_queue_size": 20,
      "api_key": "***REDACTED***"
    }
  ]
}
```

#### 3. `GET /api/instances`
**Purpose:** Real-time status of each *arr instance

**Response:**
```json
{
  "instances": [
    {
      "name": "Radarr-Movies",
      "type": "radarr",
      "enabled": true,
      "connected": true,
      "connection_error": null,
      "queue_depth": 5,
      "queue_depth_limit": 20,
      "last_search": "2026-07-18T14:15:32Z",
      "searches_today": 127,
      "search_success_rate": 0.98,
      "missing_candidates_available": 12,
      "upgrade_candidates_available": 8,
      "next_search_in_seconds": 456
    }
  ],
  "timestamp": "2026-07-18T14:23:45Z"
}
```

#### 4. `GET /api/logs?lines=100&level=INFO&search=keyword`
**Purpose:** Structured log streaming and search

**Query Parameters:**
- `lines` (int, default 100): Number of recent log lines
- `level` (str, default "INFO"): Filter by level (DEBUG, INFO, WARNING, ERROR)
- `search` (str, optional): Substring search in log messages
- `instance` (str, optional): Filter by instance name

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2026-07-18T14:23:45Z",
      "level": "INFO",
      "instance": "Radarr-Movies",
      "message": "Searching (missing): The Matrix (1/5)",
      "raw": "[2026-07-18T14:23:45Z] [INFO] [Radarr-Movies] Searching (missing): The Matrix (1/5)"
    }
  ],
  "total_count": 1523,
  "returned": 100
}
```

#### 5. `GET /api/metrics`
**Purpose:** Historical aggregated metrics (per-instance and global)

**Response:**
```json
{
  "global": {
    "total_searches_triggered": 5230,
    "searches_today": 247,
    "searches_this_hour": 18,
    "last_cycle_duration_ms": 127,
    "avg_cycle_duration_ms": 134,
    "failed_searches_today": 5,
    "retry_skips_today": 89,
    "tag_filtered_out_today": 12
  },
  "per_instance": {
    "Radarr-Movies": {
      "searches_triggered": 2150,
      "searches_today": 127,
      "missing_searches": 847,
      "upgrade_searches": 303,
      "season_pack_searches": 0,
      "failed_searches_today": 2,
      "avg_items_per_cycle": 3.2,
      "connection_failures": 0
    },
    "Sonarr-TV": {
      "searches_triggered": 1890,
      "searches_today": 85,
      "missing_searches": 650,
      "upgrade_searches": 240,
      "season_pack_searches": 15,
      "failed_searches_today": 1,
      "avg_items_per_cycle": 2.8,
      "connection_failures": 1
    }
  },
  "timestamp": "2026-07-18T14:23:45Z"
}
```

#### 6. `POST /api/search/trigger` (Optional)
**Purpose:** Manually trigger a search cycle

**Request Body:**
```json
{
  "type": "missing",  // or "upgrade" or "both"
  "instances": ["Radarr-Movies"],  // null = all enabled
  "dry_run": false
}
```

**Response:**
```json
{
  "status": "scheduled",
  "message": "Search cycle queued (will run within 1s)",
  "cycle_id": "manual_1234567890"
}
```

#### 7. `GET /api/health`
**Purpose:** Minimal liveness probe for Kubernetes/Docker

**Response:**
```json
{"status": "ok", "version": "0.10.0"}
```

---

## API Testing & Validation

### Postman Collection Structure

The Postman collection provides comprehensive testing coverage for all API endpoints. Located in `postman/Rangarr-API.postman_collection.json` (v2.1 format).

#### Collection Folders

```
Rangarr-API (Collection)
├── Health & Status
│   ├── GET /health
│   ├── GET /status
│   └── GET /instances
├── Configuration
│   └── GET /config
├── Logs & Monitoring
│   ├── GET /logs (basic)
│   ├── GET /logs (with filters)
│   ├── GET /logs (search)
│   └── GET /logs (by instance)
├── Metrics & Analytics
│   └── GET /metrics
└── Control & Actions
    └── POST /search/trigger
```

#### Example Request: GET /api/logs

```http
GET http://{{base_url}}/api/logs?lines=100&level=INFO&search=searched&instance=Radarr-Movies
Content-Type: application/json
X-Api-Key: {{api_key}}

# Pre-request Script: Log request timestamp
console.log(`[${new Date().toISOString()}] Fetching logs...`);

# Tests: Validate response
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response contains logs array", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('logs');
    pm.expect(jsonData.logs).to.be.an('array');
});

pm.test("Each log has required fields", function () {
    var jsonData = pm.response.json();
    jsonData.logs.forEach(function (log) {
        pm.expect(log).to.have.property('timestamp');
        pm.expect(log).to.have.property('level');
        pm.expect(log).to.have.property('message');
    });
});
```

#### Environment Variables

**Development:**
```json
{
  "base_url": "http://localhost:9000",
  "api_key": "dev-key-12345",
  "poll_interval_ms": "2000"
}
```

**Production:**
```json
{
  "base_url": "http://rangarr.example.com:9000",
  "api_key": "{{user_api_key}}",
  "poll_interval_ms": "2000"
}
```

#### Using Newman for CI/CD

```bash
# Install Newman
npm install -g newman

# Run collection tests
newman run postman/Rangarr-API.postman_collection.json \
  -e postman/Rangarr-Environments.postman_environment.json \
  --environment Development \
  --reporters cli,json \
  --reporter-json-export test-results.json

# Run with specific iterations
newman run postman/Rangarr-API.postman_collection.json \
  -e postman/Rangarr-Environments.postman_environment.json \
  -n 5 \
  --delay-request 500  # 500ms between requests
```

#### Test Coverage Goals

| Endpoint | Method | Tests | Coverage |
|----------|--------|-------|----------|
| `/health` | GET | Status code, response structure | 100% |
| `/status` | GET | Status code, field presence, data types | 100% |
| `/config` | GET | Status code, redacted secrets, instance count | 100% |
| `/instances` | GET | Status code, per-instance fields, connection status | 100% |
| `/logs` | GET | Status code, filtering (level, search, instance), pagination | 95% |
| `/metrics` | GET | Status code, global/per-instance aggregation, timestamps | 100% |
| `/search/trigger` | POST | Status code, dry-run validation, response format | 80% |

#### Maintenance & Versioning

- **Export frequency:** Auto-export after every API endpoint change
- **Version tracking:** Include API version in collection (`v1`, `v2`, etc.)
- **Changelog:** Maintain `postman/CHANGES.md` documenting endpoint modifications
- **Backward compatibility:** Mark deprecated endpoints; provide migration guide

---

## Feature Requirements

### Phase 1: MVP (Launch)

#### Dashboard Page (Home)
- **System Status Card**
  - Running/paused state
  - Uptime
  - Current cycle number
  - Next scheduled cycles (missing + upgrade)
- **Quick Stats**
  - Total searches triggered (all-time)
  - Searches today
  - Searches this hour
- **Instance Summary Table**
  - Instance name, type, enabled status
  - Connected / connection error
  - Queue depth / limit
  - Last search time (relative)
  - Searches today count
- **Live Activity Feed**
  - Last 10 log lines from all instances
  - Auto-refresh every 2 seconds
  - Color-coded by log level

#### Instances Page
- **Per-Instance Details**
  - Configuration (type, host, weight, batch overrides)
  - Connection status + last error (if any)
  - Queue depth chart (last 24h)
  - Today's search breakdown (missing vs upgrade vs season pack)
  - Success rate (last 24h)
  - Missing/upgrade candidates available
- **Search History (Per Instance)**
  - Last 20 searches (with timestamp, type, title, success)
  - Filter by search type
  - Sort options

#### Logs Page
- **Live Log Viewer**
  - Scrollable log output (auto-scroll option)
  - Filter by level (DEBUG, INFO, WARNING, ERROR)
  - Filter by instance name
  - Search/substring match
  - Copy log button
  - Tail mode (follow logs as they arrive)
- **Log Statistics**
  - Error count (today/week)
  - Warning count
  - Most common errors
- **Log Export** (optional)
  - Export last N lines as .txt or .json

#### Configuration Page (Read-Only)
- **Global Settings Display**
  - Intervals, batch sizes, stagger, search order, active hours
  - Formatted nicely with explanations
- **Instance List**
  - All configured instances with full settings
  - API keys redacted (show as ••••)
- **Validation Summary**
  - Green/yellow/red indicators for common misconfigs
  - Warnings: e.g., "Dry run enabled", "Active hours restrict to X-Y"

#### Metrics Page
- **Historical Charts**
  - Searches/hour over last 24h (line chart)
  - Searches/day over last 7d (bar chart)
  - Per-instance search distribution (pie chart)
  - Queue depth over time (per instance, area chart)
  - Success rate over time (line chart)
- **Key Metrics Summary**
  - Total searches today
  - Failed searches today + rate
  - Avg cycle duration
  - Failed connections (per instance)

### Phase 2: Enhancement (v1.1+)

- **Manual Search Trigger**
  - Button to trigger missing/upgrade/both searches
  - Instance selector
  - Dry-run checkbox
- **Advanced Log Filtering**
  - Date range selector
  - Multiple instance multi-select
  - Regex search (optional)
- **Alerts/Notifications**
  - Alert when instance offline
  - Alert on high error rate
  - Alert on queue buildup (optional)
- **Dark/Light Theme Toggle**
- **Responsive Mobile View**
- **Keyboard Shortcuts** (e.g., 'l' for logs, 'd' for dashboard)

---

## Implementation Tasks

**Total Tasks:** 11 core + 1 API testing = 12

### Task 1: Setup Rangarr API Layer (rangarr core)
**Owner:** This repo  
**Effort:** 4 hours  
**Status:** 🔄 IN PROGRESS (Core API implemented, testing & refinement pending)

#### ✅ Completed
- [x] Create `rangarr/api.py` with FastAPI (~350 lines)
- [x] Implement `/api/health` endpoint
- [x] Implement `/api/status` endpoint (read cycle state)
- [x] Implement `/api/config` endpoint (redact secrets)
- [x] Implement `/api/instances` endpoint (poll each client)
- [x] Implement `/api/logs` endpoint (structured JSON log sink)
- [x] Implement `/api/metrics` endpoint (track counters)
- [x] Add mandatory API key validation (X-Api-Key header required)
- [x] Start FastAPI server in daemon thread on `0.0.0.0:9000` if enabled
- [x] Add API state initialization in main.py
- [x] Add JSON logging handler for API consumption
- [x] Initialize per-instance metrics tracking
- [x] Enable automatic OpenAPI/Swagger docs at `/docs` and `/redoc`
- [x] Update requirements.txt and pyproject.toml

#### ⏳ Remaining
- [ ] Implement POST /api/search/trigger endpoint (currently returns 501)
- [ ] Generate or require API key configuration (currently uses env var with default)
- [ ] Add cycle duration history tracking for `/api/metrics` averaging
- [ ] Track retry skips and tag filters in metrics
- [ ] Create comprehensive API documentation/README
- [ ] Add unit tests for API endpoints
- [ ] Test with real rangarr instance and *arr clients

#### Environment Variables Added
```bash
RANGARR_API_ENABLED=true          # Enable/disable API server
RANGARR_API_PORT=9000             # Port to listen on
RANGARR_API_KEY=rangarr-key-123   # Required API key for all requests
```

**Dependencies Added:**
```
fastapi>=0.104
uvicorn[standard]>=0.24
```

---

### Task 2: Project Setup (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 2 hours

- [ ] Initialize Vite React TypeScript project
- [ ] Setup Tailwind CSS + shadcn/ui
- [ ] Configure absolute imports (`@/`)
- [ ] Setup ESLint + Prettier
- [ ] Create `.env.example` with `VITE_RANGARR_API_URL=http://localhost:9000`
- [ ] Setup Docker build (multi-stage: Node build + Nginx serve)
- [ ] Create `docker-compose.yml` for local dev (rangarr + rangarr-ui)
- [ ] Write README with setup, config, deployment

**Package Dependencies:**
```json
{
  "react": "^18.3",
  "react-router-dom": "^6.x",
  "@tanstack/react-query": "^5.x",
  "zustand": "^4.x",
  "axios": "^1.6",
  "recharts": "^2.x",
  "lucide-react": "^0.x",
  "tailwindcss": "^3.x",
  "@headlessui/react": "^1.x",
  "typescript": "^5.x"
}
```

---

### Task 3: API Client & Hooks (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 3 hours

- [ ] Create `frontend/api/client.ts`
  - Axios instance with base URL from `VITE_RANGARR_API_URL`
  - Global error handling
  - Retry logic for network errors
- [ ] Create `frontend/hooks/useRangarrAPI.ts`
  - `useStatus()` - GET /api/status (poll every 2s)
  - `useInstances()` - GET /api/instances (poll every 3s)
  - `useLogs(filter?)` - GET /api/logs
  - `useMetrics()` - GET /api/metrics (poll every 10s)
  - `useConfig()` - GET /api/config (once at startup)
  - `useTriggerSearch()` - POST /api/search/trigger (mutation)
- [ ] Create `frontend/hooks/useMetrics.ts`
  - Data transformation helpers
  - Calculations (success rate, avg duration, etc.)
- [ ] Create global error boundary + toast notifications
- [ ] Setup React Query with sensible defaults

---

### Task 4: Layout & Navigation (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 2 hours

- [ ] Create `frontend/components/Header.tsx`
  - Logo, title
  - Connection status indicator (green/red dot)
  - Last updated timestamp
  - Theme toggle (optional v2)
- [ ] Create `frontend/components/Sidebar.tsx`
  - Navigation menu (Dashboard, Instances, Logs, Metrics, Config)
  - Collapse button
  - Footer with version
- [ ] Create `frontend/layouts/MainLayout.tsx`
  - Wrapper with header + sidebar + content area
- [ ] Setup React Router with route structure
- [ ] Create *arr-inspired dark theme in `frontend/styles/theme.ts`

---

### Task 5: Dashboard Page (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 4 hours

- [ ] Create `frontend/pages/Dashboard.tsx`
- [ ] Create `frontend/components/StatusCard.tsx`
  - Display running state, uptime, cycle info
  - Visual indicators (spinner if running, pause icon if not)
- [ ] Create `frontend/components/QuickStatsPanel.tsx`
  - Grid of key metrics (today's searches, all-time, this hour)
- [ ] Create `frontend/components/InstanceSummaryTable.tsx`
  - Sortable/filterable table
  - Columns: name, type, status, queue, last search, searches today
  - Click row to go to instance detail page
- [ ] Create `frontend/components/LiveActivityFeed.tsx`
  - Auto-refresh log viewer
  - Show last 10 logs, color by level
  - Link to full log page

---

### Task 6: Instances Page (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 5 hours

- [ ] Create `frontend/pages/Instances.tsx`
- [ ] Create `frontend/components/InstanceDetail.tsx`
  - Header with instance name, type, status
  - Configuration section (read-only, nicely formatted)
  - Queue depth indicator + limit
  - Candidates available (missing/upgrade counts)
- [ ] Create `frontend/components/QueueChart.tsx`
  - Area chart: queue depth over last 24h
  - Recharts component
- [ ] Create `frontend/components/SearchBreakdown.tsx`
  - Pie or donut chart: missing vs upgrade vs season pack
  - Per-instance breakdown
- [ ] Create `frontend/components/SearchHistory.tsx`
  - Table of last 20 searches
  - Columns: timestamp, type, title, result (success/fail)
  - Pagination or lazy load
  - Filter by type

---

### Task 7: Logs Page (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 4 hours

- [ ] Create `frontend/pages/Logs.tsx`
- [ ] Create `frontend/components/LogViewer.tsx`
  - Scrollable log output
  - Auto-scroll toggle
  - Copy button (copy visible logs)
- [ ] Create `frontend/components/LogFilter.tsx`
  - Level dropdown (DEBUG, INFO, WARNING, ERROR)
  - Instance multi-select
  - Search/substring input
  - Clear filters button
- [ ] Create `frontend/components/LogStats.tsx`
  - Error count (today, this week)
  - Warning count
  - Most common error messages
- [ ] Implement live update (poll /api/logs every 1s)
- [ ] (Optional v2) Implement WebSocket for streaming logs

---

### Task 8: Metrics Page (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 4 hours

- [ ] Create `frontend/pages/Metrics.tsx`
- [ ] Create `frontend/components/SearchesPerHourChart.tsx`
  - Line chart: searches/hour over last 24h
- [ ] Create `frontend/components/SearchesPerDayChart.tsx`
  - Bar chart: searches/day over last 7d
- [ ] Create `frontend/components/InstanceDistributionChart.tsx`
  - Pie chart: search distribution across instances
- [ ] Create `frontend/components/SuccessRateChart.tsx`
  - Line chart: success rate over time
- [ ] Create `frontend/components/MetricsSummary.tsx`
  - Key stats (today's searches, failed, avg duration, etc.)

---

### Task 9: Config Page (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 2 hours

- [ ] Create `frontend/pages/Config.tsx`
- [ ] Create `frontend/components/GlobalConfig.tsx`
  - Display all global settings in a readable format
  - Grouped sections (Intervals, Batching, Search, Retry, etc.)
- [ ] Create `frontend/components/InstanceConfig.tsx`
  - Display all instance settings (redacted keys)
  - Per-instance cards
- [ ] Create `frontend/components/ConfigWarnings.tsx`
  - Highlight potential issues (dry run enabled, active hours restrictive, etc.)

---

### Task 10: Docker & Deployment (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 2 hours

- [ ] Create `Dockerfile` (multi-stage: build + serve)
  - Stage 1: Node alpine, build React app
  - Stage 2: Nginx alpine, serve static files
  - Copy nginx config for SPA routing
- [ ] Create `docker-compose.yml` for local testing
- [ ] Create `.dockerignore`
- [ ] Document environment variables
- [ ] Document port mappings (default port 3000 or 80)

---

### Task 11a: Postman Collection & API Testing (rangarr core)
**Owner:** This repo  
**Effort:** 2 hours

- [ ] Create `postman/Rangarr-API.postman_collection.json`
  - All 7 API endpoints with example requests
  - Request descriptions and parameter documentation
  - Example response bodies (mock data)
  - Environment variables for `base_url`, `api_key` (optional)
  - Folder structure: Health, Status, Config, Instances, Logs, Metrics, Search
- [ ] Create `postman/Rangarr-Environments.postman_environment.json`
  - Development environment (localhost:9000)
  - Production environment (template with user substitution)
  - Variables: `base_url`, `api_key`, `poll_interval_ms`
- [ ] Create `postman/README.md`
  - How to import collection into Postman
  - How to set up environments
  - Example workflows (query logs, check status, trigger search)
  - Screenshot of collection structure
- [ ] Add Postman collection export to CI/CD (auto-update on API changes)
- [ ] Document collection versioning strategy

**Format:** Postman Collection v2.1 (JSON)

**Usage Example:**
```bash
# Import into Postman GUI, or use Newman CLI:
newman run postman/Rangarr-API.postman_collection.json \
  -e postman/Rangarr-Environments.postman_environment.json \
  -n 7  # Run 7 iterations
```

---

### Task 11b: Documentation & Testing (rangarr-ui)
**Owner:** rangarr-ui repo  
**Effort:** 3 hours

- [ ] Write comprehensive README
  - Installation (local dev, Docker)
  - Configuration (env vars)
  - Features overview
  - Screenshots/GIFs
  - Troubleshooting
- [ ] Add JSDoc comments to all components
- [ ] Create contributing guide
- [ ] Link to Postman collection in API docs
- [ ] (Optional) Add Vitest unit tests for API hooks
- [ ] (Optional) Add Cypress E2E tests for critical flows

---

## Design Specifications

### Color Palette (Inspired by *arr Stack)

```css
/* Dark theme (primary) */
--color-primary: #1a1a2e       /* Deep navy */
--color-surface: #16213e       /* Darker navy */
--color-accent: #0f3460        /* Blue accent */
--color-success: #00d084       /* Green */
--color-warning: #ffa500       /* Orange */
--color-error: #e74c3c         /* Red */
--color-text-primary: #ecf0f1  /* Light gray */
--color-text-secondary: #bdc3c7 /* Lighter gray */
--color-border: #2c3e50        /* Dark blue-gray */
```

### Typography

- **Headers:** Inter or Roboto (sans-serif)
- **Body:** Same as headers
- **Monospace:** Fira Code or Monaco (for logs)

### Component Patterns

- **Cards:** Subtle border + shadow, dark background
- **Tables:** Striped rows (alternating opacity), hover highlight
- **Charts:** Dark background, colored data lines, grid lines faint
- **Status Indicators:** Solid circles (green/red/yellow)
- **Buttons:** Filled (primary), outlined (secondary), minimal spacing

### Responsive Breakpoints

- **Mobile:** < 640px (sidebar collapses to icon)
- **Tablet:** 640px - 1024px (sidebar narrow)
- **Desktop:** > 1024px (full layout)

---

## Deployment

### Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  rangarr:
    image: judochinx/rangarr:latest
    container_name: rangarr
    environment:
      LOG_LEVEL: INFO
      RANGARR_API_ENABLED: 'true'
      RANGARR_API_PORT: 9000
    ports:
      - "9000:9000"  # API
    volumes:
      - ./config.yaml:/app/config/config.yaml:ro
    networks:
      - rangarr-net

  rangarr-ui:
    image: rangarr-ui:latest
    container_name: rangarr-ui
    environment:
      VITE_RANGARR_API_URL: http://rangarr:9000
    ports:
      - "3000:80"  # Web UI
    depends_on:
      - rangarr
    networks:
      - rangarr-net

  # Optional: Radarr, Sonarr, etc. on same network
  radarr:
    image: lscr.io/linuxserver/radarr:latest
    ...

networks:
  rangarr-net:
    driver: bridge
```

### Environment Variables

```bash
# .env (frontend build)
VITE_RANGARR_API_URL=http://localhost:9000
VITE_POLL_INTERVAL_MS=2000
VITE_LOG_LINES_DEFAULT=100
VITE_THEME_MODE=dark

# rangarr container
RANGARR_API_ENABLED=true
RANGARR_API_PORT=9000
RANGARR_API_HOST=0.0.0.0
```

### Kubernetes (Optional)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rangarr-ui
spec:
  ports:
  - port: 80
    targetPort: 3000
  selector:
    app: rangarr-ui
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rangarr-ui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rangarr-ui
  template:
    metadata:
      labels:
        app: rangarr-ui
    spec:
      containers:
      - name: rangarr-ui
        image: rangarr-ui:latest
        env:
        - name: VITE_RANGARR_API_URL
          value: http://rangarr:9000
        ports:
        - containerPort: 3000
```

---

## Success Criteria

- [ ] Dashboard loads in < 2s over local network
- [ ] Live updates (logs, status) refresh within 2-3s
- [ ] All charts render smoothly with sample data
- [ ] Mobile responsive (breakpoints tested)
- [ ] Dark theme matches *arr aesthetic
- [ ] Accessible (WCAG AA compliance)
- [ ] No console errors or warnings
- [ ] Can run in Docker alongside rangarr
- [ ] **Postman collection importable and all requests working**
- [ ] API endpoints tested via collection (manual or Newman CLI)
- [ ] OpenAPI docs accessible at `/docs`
- [ ] Documentation complete + examples
- [ ] Ready for community contribution

---

## Open Questions

1. **Authentication:** Should UI require API key? (v1 = no, v2 = yes)
2. **Real-time logs:** Polling vs WebSocket? (v1 = polling, v2 = WebSocket)
3. **Manual search trigger:** Must-have or nice-to-have? (v1 = read-only, v2 = with trigger)
4. **Database:** Persist metrics/history locally? (v1 = no, metrics in memory)
5. **Branding:** Use rangarr logo/colors or create new visual identity?

---

## Timeline Estimate

- **Phase 1 (MVP):** 45-55 hours
  - API layer (rangarr): 4h
  - Postman collection (rangarr): 2h
  - Project setup (UI): 2h
  - API hooks (UI): 3h
  - Layout (UI): 2h
  - Dashboard (UI): 4h
  - Instances (UI): 5h
  - Logs (UI): 4h
  - Metrics (UI): 4h
  - Config (UI): 2h
  - Docker (UI): 2h
  - Docs & Testing (UI): 3h
  - Buffer: ~8h

- **Phase 2 (v1.1):** 15-20 hours
  - Manual search trigger
  - Advanced log filtering
  - Alerts/notifications
  - Mobile responsiveness
  - Theme toggle

---

## Next Steps

1. Review and approve this plan
2. Create issue/branch in rangarr repo for API layer
3. Initialize rangarr-ui project
4. Begin Task 1 & 2 in parallel
5. Set up demo environment for testing
6. Gather user feedback on UI mockups (optional)
7. Begin implementation

