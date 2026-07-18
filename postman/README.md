# Rangarr API - Postman Collection

Complete REST API testing collection for Rangarr orchestration service. Test all 7 endpoints with built-in validations, mock responses, and environment-based configuration.

---

## Quick Start

### 1. Import into Postman

**Option A: Import from file**
- Open Postman
- Click **Import** (top-left)
- Select `Rangarr-API.postman_collection.json`
- Click **Import**

**Option B: Import environments**
- Click **Environments** (left sidebar)
- Click **Import** 
- Select `Rangarr-Environments.postman_environment.json`

### 2. Select Environment

- Click environment dropdown (top-right)
- Select **Development** or **Production**

### 3. Make Your First Request

- Click **Health & Status** → **GET /api/health**
- Click **Send**
- See response with status and version

---

## Collection Structure

```
Rangarr API (v1.0.0)
├── Health & Status
│   ├── GET /health              → Liveness probe
│   ├── GET /status              → Cycle info, uptime, searches
│   └── GET /instances           → Per-instance status
│
├── Configuration
│   └── GET /config              → Full config (secrets redacted)
│
├── Logs & Monitoring
│   ├── GET /logs (basic)        → Last 100 lines
│   ├── GET /logs (level filter) → Filter by severity (WARNING, ERROR)
│   ├── GET /logs (search)       → Substring search
│   └── GET /logs (by instance)  → Filter by instance name
│
├── Metrics & Analytics
│   └── GET /metrics             → Global + per-instance statistics
│
└── Control & Actions
    └── POST /search/trigger     → Manual search (optional)
```

---

## Endpoints

### Health & Status

#### `GET /api/health`
Minimal health check for orchestration/monitoring systems.

**Response:**
```json
{
  "status": "ok",
  "version": "0.10.0"
}
```

---

#### `GET /api/status`
Current rangarr state: cycle info, uptime, search counts, next scheduled cycles.

**Response:**
```json
{
  "running": true,
  "uptime_seconds": 86400,
  "uptime_str": "1d 0h 0m",
  "current_cycle": 342,
  "next_missing_in_seconds": 1234,
  "next_upgrade_in_seconds": 2345,
  "last_cycle_duration_ms": 127,
  "total_searches_triggered": 5230,
  "searches_today": 247,
  "failed_searches_today": 5,
  "dry_run_mode": false,
  "active_hours_active": true,
  "timestamp": "2026-07-18T14:23:45Z"
}
```

---

#### `GET /api/instances`
Real-time status of each *arr instance (Radarr, Sonarr, Lidarr, Readarr, Whisparr).

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

---

### Configuration

#### `GET /api/config`
Complete configuration snapshot. All API keys and passwords are redacted with `***REDACTED***`.

**Response:**
```json
{
  "global": {
    "interval_minutes": 60,
    "dry_run": false,
    "active_hours": "22:00-06:00",
    ...
  },
  "instances": [
    {
      "name": "Radarr-Movies",
      "type": "radarr",
      "host": "http://radarr:7878",
      "api_key": "***REDACTED***"
    }
  ]
}
```

---

### Logs & Monitoring

#### `GET /api/logs`

Retrieve and filter structured logs.

**Query Parameters:**
- `lines` (int, default: 100) - Number of recent log lines to return
- `level` (string, default: INFO) - Filter by level: DEBUG, INFO, WARNING, ERROR
- `search` (string, optional) - Substring search in log messages
- `instance` (string, optional) - Filter by instance name (e.g., "Radarr-Movies")

**Examples:**
```bash
# Last 100 logs, INFO and above
GET /api/logs

# Last 50 WARNING/ERROR logs
GET /api/logs?lines=50&level=WARNING

# Search for "searched" in logs
GET /api/logs?search=searched

# Logs from Radarr-Movies only
GET /api/logs?instance=Radarr-Movies&lines=50
```

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2026-07-18T14:23:45Z",
      "level": "INFO",
      "instance": "Radarr-Movies",
      "message": "Searching (missing): The Matrix (1/5)"
    }
  ],
  "total_count": 1523,
  "returned": 100
}
```

---

### Metrics & Analytics

#### `GET /api/metrics`

Aggregated search statistics and performance metrics.

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
    }
  },
  "timestamp": "2026-07-18T14:23:45Z"
}
```

---

### Control & Actions

#### `POST /api/search/trigger`

Manually trigger a search cycle (optional endpoint, currently returns 501 Not Implemented).

**Request Body:**
```json
{
  "type": "missing",
  "instances": ["Radarr-Movies"],
  "dry_run": false
}
```

**Parameters:**
- `type` (string): `"missing"`, `"upgrade"`, or `"both"`
- `instances` (array or null): Instance names to search, or `null` for all enabled
- `dry_run` (boolean): If true, plan search but don't execute

**Response (when implemented):**
```json
{
  "status": "scheduled",
  "message": "Search cycle queued (will run within 1s)",
  "cycle_id": "manual_1234567890"
}
```

---

## Authentication

All endpoints require the **X-Api-Key** header with a valid API key.

```
X-Api-Key: {{api_key}}
```

**Missing key:** Returns `401 Unauthorized`  
**Invalid key:** Returns `403 Forbidden`

The collection includes the header automatically when you set the `api_key` environment variable.

---

## Using Environments

### Development Environment
```json
{
  "base_url": "http://localhost:9000",
  "api_key": "rangarr-default-key",
  "poll_interval_ms": "2000"
}
```

Switch to **Development** to test locally with the default API key.

### Production Environment
```json
{
  "base_url": "http://rangarr.example.com:9000",
  "api_key": "your-production-api-key-here",
  "poll_interval_ms": "2000"
}
```

**Before using:**
1. Click **Environments** (left sidebar)
2. Select **Production**
3. Edit values: change `base_url` and `api_key` to your production credentials
4. Save

---

## CLI Testing with Newman

Test the collection programmatically using Newman.

### Install Newman
```bash
npm install -g newman
```

### Run All Tests (Development)
```bash
newman run Rangarr-API.postman_collection.json \
  -e Rangarr-Environments.postman_environment.json \
  --environment Development
```

### Run with Iterations
```bash
newman run Rangarr-API.postman_collection.json \
  -e Rangarr-Environments.postman_environment.json \
  -n 5 \
  --delay-request 500  # 500ms between requests
```

### Generate HTML Report
```bash
newman run Rangarr-API.postman_collection.json \
  -e Rangarr-Environments.postman_environment.json \
  -r html --reporter-html-export report.html
```

---

## Common Workflows

### Workflow 1: Monitor System Health
1. **GET /api/health** → Verify API is running
2. **GET /api/status** → Check uptime and cycle info
3. **GET /api/instances** → View per-instance status
4. **GET /api/metrics** → Review today's search stats

### Workflow 2: Diagnose Issues
1. **GET /api/instances** → Identify offline/failing instances
2. **GET /api/logs?level=ERROR** → View recent errors
3. **GET /api/logs?instance=Radarr-Movies** → Filter by failing instance
4. **GET /api/config** → Review configuration

### Workflow 3: Dashboard Development
1. **GET /api/status** → Every 2 seconds (polling interval)
2. **GET /api/instances** → Every 3 seconds
3. **GET /api/logs** → Every 1 second (live feed)
4. **GET /api/metrics** → Every 10 seconds

---

## Error Handling

### Common Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | Success | Valid request with response |
| `400` | Bad Request | Invalid query parameters |
| `401` | Unauthorized | Missing `X-Api-Key` header |
| `403` | Forbidden | Invalid/wrong API key |
| `404` | Not Found | Endpoint doesn't exist |
| `500` | Server Error | Rangarr API error |
| `501` | Not Implemented | `/api/search/trigger` (placeholder) |

### Error Response Format
```json
{
  "detail": "Invalid API key"
}
```

---

## Troubleshooting

### "Connection refused" error
- Verify rangarr API is running: `http://localhost:9000/api/health`
- Check environment variables: `RANGARR_API_ENABLED=true`, `RANGARR_API_PORT=9000`

### "401 Unauthorized"
- Ensure `X-Api-Key` header is present
- Verify `{{api_key}}` variable is set correctly in selected environment

### "403 Forbidden"
- API key is incorrect or doesn't match `RANGARR_API_KEY` env var
- Check rangarr logs for key mismatch errors

### Empty or unexpected responses
- Verify rangarr has been running long enough to collect data
- Check that instances are configured and connected
- Review rangarr logs for any initialization errors

---

## Collection Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-18 | Initial release with 7 endpoints |

**Next versions will track:**
- New endpoints
- Parameter changes
- Response schema updates
- Breaking changes

---

## Support & Documentation

- **API Documentation:** See [API.md](../rangarr/API.md) in the rangarr repo
- **OpenAPI/Swagger UI:** http://localhost:9000/docs (when API running)
- **ReDoc:** http://localhost:9000/redoc
- **GitHub Issues:** Report bugs or feature requests

---

## License

Same as Rangarr project. See [LICENSE](../LICENSE) in root.
