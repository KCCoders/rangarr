"""REST API for Rangarr orchestration service.

Provides read-only endpoints for dashboard/UI consumption, with mandatory API key authentication.
All endpoints are designed to be lightweight and non-blocking to the orchestration loop.
"""

import datetime
import logging
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

logger = logging.getLogger(__name__)

_API_VERSION = '1.0.0'


class APIState:
    """Thread-safe container for API state (metrics, logs, config).

    Used to communicate between orchestration loop and API endpoints.
    """

    def __init__(self) -> None:
        """Initialize empty state."""
        self.uptime_start = datetime.datetime.now(datetime.UTC)
        self.cycle_count = 0
        self.last_cycle_duration_ms = 0
        self.total_searches_triggered = 0
        self.searches_today = 0
        self.failed_searches_today = 0
        self.next_missing_in_seconds: float = 0
        self.next_upgrade_in_seconds: float = 0
        self.dry_run_mode = False
        self.active_hours_active = True
        self.logs: list[dict[str, Any]] = []
        self.instance_metrics: dict[str, dict[str, Any]] = {}
        self.config: dict[str, Any] = {}


def _get_api_key(
    x_api_key: str = Header(alias='X-Api-Key'),
) -> str:
    """Retrieve API key from request header.

    Args:
        x_api_key: API key from X-Api-Key header.

    Returns:
        The API key string.

    Raises:
        HTTPException: If API key header is missing.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing X-Api-Key header',
            headers={'WWW-Authenticate': 'ApiKey'},
        )
    return x_api_key


def _log_request(method: str, endpoint: str, client_ip: str | None = None) -> None:
    """Log API request for auditing."""
    client_str = f' from {client_ip}' if client_ip else ''
    logger.debug(f'API {method} {endpoint}{client_str}')


def _uptime_str(seconds: float) -> str:
    """Format uptime in human-readable form (e.g., '1d 5h 23m')."""
    td = datetime.timedelta(seconds=int(seconds))
    parts = []
    if td.days:
        parts.append(f'{td.days}d')
    hours = td.seconds // 3600
    if hours:
        parts.append(f'{hours}h')
    minutes = (td.seconds % 3600) // 60
    if minutes or not parts:
        parts.append(f'{minutes}m')
    return ' '.join(parts)


def create_api_app(
    state: APIState,
    api_key: str,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        state: Shared API state container (updated by orchestration loop).
        api_key: Required API key for all endpoints (validated on each request).

    Returns:
        Configured FastAPI application ready to mount or run.
    """
    app = FastAPI(
        title='Rangarr API',
        version=_API_VERSION,
        description='REST API for Rangarr orchestration service',
        docs_url='/docs',
        redoc_url='/redoc',
        openapi_url='/openapi.json',
    )

    # Store API key in app state for validation
    app.state.rangarr_api_key = api_key
    app.state.rangarr_state = state

    def _validate_api_key(key_header: str = Depends(_get_api_key)) -> str:
        """Validate API key matches configured key."""
        if key_header != app.state.rangarr_api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid API key',
            )
        return key_header

    # Create router with all endpoints
    router = APIRouter(prefix='/api', tags=['rangarr'])

    @router.get('/health', tags=['health'])
    def health(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Health check / liveness probe.

        Returns:
            Status and version information.
        """
        return {
            'status': 'ok',
            'version': _API_VERSION,
        }

    @router.get('/status', tags=['status'])
    def get_status(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Current rangarr status and cycle information.

        Returns:
            Dictionary containing running state, cycle info, and next scheduled times.
        """
        rangarr_state = app.state.rangarr_state
        uptime_secs = (datetime.datetime.now(datetime.UTC) - rangarr_state.uptime_start).total_seconds()
        return {
            'running': True,  # TODO: Track actual pause state if implemented
            'uptime_seconds': int(uptime_secs),
            'uptime_str': _uptime_str(uptime_secs),
            'current_cycle': rangarr_state.cycle_count,
            'next_missing_in_seconds': int(rangarr_state.next_missing_in_seconds),
            'next_upgrade_in_seconds': int(rangarr_state.next_upgrade_in_seconds),
            'last_cycle_duration_ms': rangarr_state.last_cycle_duration_ms,
            'total_searches_triggered': rangarr_state.total_searches_triggered,
            'searches_today': rangarr_state.searches_today,
            'failed_searches_today': rangarr_state.failed_searches_today,
            'dry_run_mode': rangarr_state.dry_run_mode,
            'active_hours_active': rangarr_state.active_hours_active,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat() + 'Z',
        }

    @router.get('/config', tags=['configuration'])
    def get_config(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Current configuration (secrets redacted).

        Returns:
            Configuration dictionary with API keys masked.
        """
        rangarr_state = app.state.rangarr_state
        if not rangarr_state.config:
            return {'error': 'Configuration not yet initialized'}

        # Deep copy and redact secrets
        config = _redact_secrets(rangarr_state.config)
        return config

    @router.get('/instances', tags=['instances'])
    def get_instances(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Real-time status of all configured *arr instances.

        Returns:
            Dictionary containing per-instance status and metrics.
        """
        rangarr_state = app.state.rangarr_state
        instances = []

        for name, metrics in rangarr_state.instance_metrics.items():
            instances.append({
                'name': name,
                'type': metrics.get('type', 'unknown'),
                'enabled': metrics.get('enabled', False),
                'connected': metrics.get('connected', False),
                'connection_error': metrics.get('connection_error'),
                'queue_depth': metrics.get('queue_depth', 0),
                'queue_depth_limit': metrics.get('queue_depth_limit', 0),
                'last_search': metrics.get('last_search'),
                'searches_today': metrics.get('searches_today', 0),
                'search_success_rate': metrics.get('search_success_rate', 1.0),
                'missing_candidates_available': metrics.get('missing_candidates_available', 0),
                'upgrade_candidates_available': metrics.get('upgrade_candidates_available', 0),
                'next_search_in_seconds': max(0, int(metrics.get('next_search_in_seconds', 0))),
            })

        return {
            'instances': instances,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat() + 'Z',
        }

    @router.get('/logs', tags=['logs'])
    def get_logs(
        lines: int = Query(100, ge=1, le=10000, description='Number of recent log lines to return'),
        level: str = Query('INFO', description='Filter by log level (DEBUG, INFO, WARNING, ERROR)'),
        search: str = Query('', description='Substring search in log message'),
        instance: str = Query('', description='Filter by instance name'),
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Retrieve structured logs with optional filtering.

        Args:
            lines: Number of recent log lines (1-10000).
            level: Minimum log level filter.
            search: Substring to search in log messages.
            instance: Filter by instance name.

        Returns:
            Dictionary containing filtered log entries.
        """
        rangarr_state = app.state.rangarr_state
        level_priority = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
        min_level_priority = level_priority.get(level.upper(), 1)

        filtered = []
        for log_record in rangarr_state.logs:
            if level_priority.get(log_record.get('level', 'INFO'), 1) < min_level_priority:
                continue
            if instance and log_record.get('instance') != instance:
                continue
            if search and search.lower() not in log_record.get('message', '').lower():
                continue
            filtered.append(log_record)

        # Return last N logs
        recent = filtered[-lines:] if lines > 0 else filtered
        return {
            'logs': recent,
            'total_count': len(rangarr_state.logs),
            'returned': len(recent),
            'filters': {
                'level': level,
                'search': search,
                'instance': instance,
            },
        }

    @router.get('/metrics', tags=['metrics'])
    def get_metrics(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Historical aggregated metrics (global and per-instance).

        Returns:
            Dictionary with global and per-instance search statistics.
        """
        rangarr_state = app.state.rangarr_state
        per_instance = {}

        for name, metrics in rangarr_state.instance_metrics.items():
            per_instance[name] = {
                'searches_triggered': metrics.get('searches_triggered', 0),
                'searches_today': metrics.get('searches_today', 0),
                'missing_searches': metrics.get('missing_searches', 0),
                'upgrade_searches': metrics.get('upgrade_searches', 0),
                'season_pack_searches': metrics.get('season_pack_searches', 0),
                'failed_searches_today': metrics.get('failed_searches_today', 0),
                'avg_items_per_cycle': metrics.get('avg_items_per_cycle', 0.0),
                'connection_failures': metrics.get('connection_failures', 0),
            }

        return {
            'global': {
                'total_searches_triggered': rangarr_state.total_searches_triggered,
                'searches_today': rangarr_state.searches_today,
                'failed_searches_today': rangarr_state.failed_searches_today,
                'last_cycle_duration_ms': rangarr_state.last_cycle_duration_ms,
                'avg_cycle_duration_ms': 0,  # TODO: Calculate from cycle history
                'retry_skips_today': 0,  # TODO: Track in orchestration loop
                'tag_filtered_out_today': 0,  # TODO: Track in orchestration loop
            },
            'per_instance': per_instance,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat() + 'Z',
        }

    @router.post('/search/trigger', tags=['control'], status_code=202)
    def trigger_search(
        _: str = Depends(_validate_api_key),
    ) -> dict[str, Any]:
        """Manually trigger a search cycle (optional feature).

        Currently not implemented; returns 501 Not Implemented.
        Future implementation will support request body with:
        - type: missing/upgrade/both
        - instances: list of instance names (null = all)
        - dry_run: bool

        Returns:
            Status indicating feature is not yet implemented.
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail='Manual search triggering not yet implemented',
        )

    app.include_router(router)
    return app


def _redact_secrets(obj: Any) -> Any:
    """Recursively redact secrets (API keys) from config.

    Args:
        obj: Object to redact (dict, list, or scalar).

    Returns:
        Redacted copy of object.
    """
    if isinstance(obj, dict):
        result = {}
        for key, val in obj.items():
            if key in ('api_key', 'password', 'secret'):
                result[key] = '***REDACTED***'
            else:
                result[key] = _redact_secrets(val)
        return result
    if isinstance(obj, list):
        return [_redact_secrets(item) for item in obj]
    # Scalar values: return as-is
    return obj


def add_json_logging_handler(state: APIState, max_logs: int = 5000) -> logging.Handler:
    """Create and return a custom logging handler that stores JSON logs in API state.

    Args:
        state: APIState container to store logs in.
        max_logs: Maximum number of logs to retain (FIFO eviction).

    Returns:
        Configured logging.Handler instance.
    """

    class APILogHandler(logging.Handler):
        """Custom handler that stores structured logs in API state."""

        def emit(self, record: logging.LogRecord) -> None:
            """Format and store log record.

            Args:
                record: LogRecord to emit.
            """
            try:
                log_entry = {
                    'timestamp': datetime.datetime.fromtimestamp(
                        record.created, tz=datetime.UTC
                    ).isoformat() + 'Z',
                    'level': record.levelname,
                    'instance': record.name.split('.')[-1] if record.name else 'rangarr',
                    'message': self.format(record),
                }
                state.logs.append(log_entry)

                # FIFO eviction if we exceed max_logs
                if len(state.logs) > max_logs:
                    state.logs = state.logs[-max_logs:]
            except Exception:
                self.handleError(record)

    handler = APILogHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    handler.setFormatter(formatter)
    return handler
