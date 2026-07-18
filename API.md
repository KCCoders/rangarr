# Rangarr REST API Documentation

The Rangarr API provides read-only endpoints for dashboard/UI consumption and monitoring. All endpoints require mandatory API key authentication.

---

## Quick Start

### Enable the API

The API server is **enabled by default** on port 9000. To disable, set:
```bash
RANGARR_API_ENABLED=false
```

### Configuration

Set these environment variables to customize the API:

```bash
RANGARR_API_ENABLED=true              # Enable/disable (default: true)
RANGARR_API_PORT=9000                 # Port to listen on (default: 9000)
RANGARR_API_KEY=your-secret-key       # Required API key (default: rangarr-default-key)
```

### Authentication

All requests require the `X-Api-Key` header:

```bash
curl -H "X-Api-Key: your-secret-key" http://localhost:9000/api/health
```

---

## Endpoints

### Health Check

**`GET /api/health`**

Liveness probe for Kubernetes, Docker health checks, etc.

```bash
curl -H "X-Api-Key: your-key" http://localhost:9000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### System Status

**`GET /api/status`**

Current rangarr state and cycle information.

```bash
curl -H "X-Api-Key: your-key" http://localhost:9000/api/status
```

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

### Configuration

**`GET /api/config`**

Current configuration (API keys redacted as `***REDACTED***`).

```bash
curl -H "X-Api-Key: your-key" http://localhost:9000/api/config
```

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

---

### Instance Status

**`GET /api/instances`**

Real-time status of all configured *arr instances.

```bash
curl -H "X-Api-Key: your-key" http://localhost:9000/api/instances
```

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

### Logs

**`GET /api/logs`**

Retrieve structured logs with optional filtering.

**Query Parameters:**
- `lines` (int, default=100, max=10000): Number of recent log lines
- `level` (string, default=INFO): Filter by level (DEBUG, INFO, WARNING, ERROR)
- `search` (string, optional): Substring search in log messages
- `instance` (string, optional): Filter by instance name

```bash
# Basic: last 100 logs
curl -H "X-Api-Key: your-key" http://localhost:9000/api/logs

# Filter by level
curl -H "X-Api-Key: your-key" "http://localhost:9000/api/logs?level=ERROR"

# Search + filter
curl -H "X-Api-Key: your-key" "http://localhost:9000/api/logs?search=searched&instance=Radarr-Movies&lines=50"
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
    },
    {
      "timestamp": "2026-07-18T14:23:32Z",
      "level": "WARNING",
      "instance": "Sonarr-TV",
      "message": "[Sonarr-TV] Queue check failed; skipping this cycle."
    }
  ],
  "total_count": 1523,
  "returned": 2,
  "filters": {
    "level": "ERROR",
    "search": "",
    "instance": ""
  }
}
```

---

### Metrics

**`GET /api/metrics`**

Historical aggregated metrics (global and per-instance).

```bash
curl -H "X-Api-Key: your-key" http://localhost:9000/api/metrics
```

**Response:**
```json
{
  "global": {
    "total_searches_triggered": 5230,
    "searches_today": 247,
    "failed_searches_today": 5,
    "last_cycle_duration_ms": 127,
    "avg_cycle_duration_ms": 134,
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

---

### Manual Search Trigger (Planned)

**`POST /api/search/trigger`** *(Not yet implemented)*

Manually trigger a search cycle.

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

Currently returns `501 Not Implemented`.

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI:** `http://localhost:9000/docs`
- **ReDoc:** `http://localhost:9000/redoc`
- **OpenAPI Schema:** `http://localhost:9000/openapi.json`

---

## Example Use Cases

### Check if Rangarr is Running

```bash
curl -s -H "X-Api-Key: your-key" http://localhost:9000/api/health | jq .status
# Output: "ok"
```

### Monitor Queue Depth

```bash
curl -s -H "X-Api-Key: your-key" http://localhost:9000/api/instances | \
  jq '.instances[] | {name, queue_depth, queue_depth_limit}'
```

### Find Recent Errors

```bash
curl -s -H "X-Api-Key: your-key" "http://localhost:9000/api/logs?level=ERROR&lines=20" | \
  jq '.logs[] | {timestamp, instance, message}'
```

### Check Search Trends

```bash
curl -s -H "X-Api-Key: your-key" http://localhost:9000/api/metrics | \
  jq '{total: .global.total_searches_triggered, today: .global.searches_today, failed: .global.failed_searches_today}'
```

---

## Error Responses

### Missing API Key

```bash
curl http://localhost:9000/api/status
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Missing X-Api-Key header"
}
```

### Invalid API Key

```bash
curl -H "X-Api-Key: wrong-key" http://localhost:9000/api/status
```

**Response (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

---

## Notes for Dashboard Developers

1. **Polling Intervals:** The UI should poll endpoints at different rates:
   - `/api/status`: Every 2-3 seconds (status, cycle info)
   - `/api/instances`: Every 3-5 seconds (queue depth, last search)
   - `/api/logs`: Every 1-2 seconds (live updates)
   - `/api/metrics`: Every 10-15 seconds (historical data)

2. **Caching:** `/api/config` can be cached for the session (rarely changes).

3. **Rate Limiting:** Not implemented; deploy behind a reverse proxy if needed.

4. **Connection Errors:** If API is unreachable, the dashboard should display a connection error and retry with exponential backoff.

---

## Integration with Postman

The Rangarr API is fully documented in the Postman collection. See `postman/README.md` for import and usage instructions.

---

## Future Enhancements

- Implement POST /api/search/trigger
- Add WebSocket support for real-time log streaming
- Add per-instance search history endpoint
- Add metrics history retention (last 7 days)
- Add authentication mechanism beyond API key
