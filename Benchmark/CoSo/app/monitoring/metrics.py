from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "benchmark_http_requests_total",
    "Total number of HTTP requests handled by the API.",
    ["method", "path", "status", "app"],
)

HTTP_REQUEST_DURATION = Histogram(
    "benchmark_http_request_duration_seconds",
    "Latency of HTTP requests handled by the API.",
    ["method", "path", "app"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

CONFLICT_CHECK_DURATION = Histogram(
    "benchmark_conflict_check_duration_seconds",
    "Duration of schedule conflict check.",
    ["app"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

LOCK_HOLD_DURATION = Histogram(
    "benchmark_lock_hold_duration_seconds",
    "Duration of lock holding.",
    ["type", "app"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

DB_ERRORS_TOTAL = Counter(
    "benchmark_db_errors_total",
    "Total database errors by type.",
    ["type", "app"],
)
