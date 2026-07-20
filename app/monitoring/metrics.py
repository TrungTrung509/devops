from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import func

from configs.db import SessionLocals
from enums.status import EnrollmentTransactionState
from models.EnrollmentTransactions import EnrollmentTransaction

REPLICATION_OUTBOX_STATUSES = ("PENDING", "DONE", "FAILED")
REPLICATION_SITE_STATUSES = ("ONLINE", "OFFLINE", "ERROR", "UNKNOWN")
REPLICATION_SITE_ROLES = ("PRIMARY", "REPLICA")
ENROLLMENT_TRANSACTION_STATES = tuple(state.value for state in EnrollmentTransactionState)

HTTP_REQUESTS_TOTAL = Counter(
    "csdlpt_http_requests_total",
    "Total number of HTTP requests handled by the API.",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "csdlpt_http_request_duration_seconds",
    "Latency of HTTP requests handled by the API.",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "csdlpt_http_requests_in_progress",
    "Number of HTTP requests that are currently being processed.",
    ["method", "path"],
)
COURSE_READ_DURATION_SECONDS = Histogram(
    "csdlpt_course_read_duration_seconds",
    "Latency of course read requests grouped by read mode and site routing.",
    ["endpoint", "read_mode", "source_site", "served_site"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
COURSE_READ_REQUESTS_TOTAL = Counter(
    "csdlpt_course_read_requests_total",
    "Total number of course read requests grouped by read mode and site routing.",
    ["endpoint", "read_mode", "source_site", "served_site", "status"],
)

BACKGROUND_LOOP_FAILURES_TOTAL = Counter(
    "csdlpt_background_loop_failures_total",
    "Number of failed background loop executions.",
    ["loop"],
)
REPLICATION_RECOVERY_RUNS_TOTAL = Counter(
    "csdlpt_replication_recovery_runs_total",
    "Number of replication recovery loop executions.",
)
REPLICATION_RECOVERY_LAST_BATCH = Gauge(
    "csdlpt_replication_recovery_last_batch",
    "Last replication recovery batch summary.",
    ["result"],
)
REPLICATION_RECOVERY_LAST_RUN_UNIX_SECONDS = Gauge(
    "csdlpt_replication_recovery_last_run_unix_seconds",
    "Unix timestamp of the latest replication recovery loop execution.",
)
REPLICATION_DISPATCH_EVENTS_TOTAL = Counter(
    "csdlpt_replication_dispatch_events_total",
    "Replication events dispatched by target site and final status.",
    ["target_site", "status"],
)
REPLICATION_OUTBOX_EVENTS = Gauge(
    "csdlpt_replication_outbox_events",
    "Current number of replication outbox events by status.",
    ["status"],
)
REPLICATION_SITE_UP = Gauge(
    "csdlpt_replication_site_up",
    "Whether a replicated site is currently online.",
    ["site_id"],
)
REPLICATION_SITE_STATUS = Gauge(
    "csdlpt_replication_site_status",
    "Current replication site status as a one-hot gauge.",
    ["site_id", "status"],
)
REPLICATION_SITE_ROLE = Gauge(
    "csdlpt_replication_site_role",
    "Current replication site role as a one-hot gauge.",
    ["site_id", "role"],
)
REPLICATION_SITE_HEARTBEAT_AGE_SECONDS = Gauge(
    "csdlpt_replication_site_heartbeat_age_seconds",
    "Age in seconds since the last heartbeat observed for a site.",
    ["site_id"],
)

ENROLLMENT_3PC_RECOVERY_TOTAL = Counter(
    "csdlpt_enrollment_3pc_recovery_total",
    "Recovered 3PC outcomes produced by the recovery loop.",
    ["outcome"],
)
ENROLLMENT_3PC_RECOVERY_LAST_BATCH = Gauge(
    "csdlpt_enrollment_3pc_recovery_last_batch",
    "Last 3PC recovery batch summary.",
    ["result"],
)
ENROLLMENT_3PC_RECOVERY_LAST_RUN_UNIX_SECONDS = Gauge(
    "csdlpt_enrollment_3pc_recovery_last_run_unix_seconds",
    "Unix timestamp of the latest 3PC recovery loop execution.",
)
ENROLLMENT_3PC_SITE_UP = Gauge(
    "csdlpt_enrollment_3pc_site_up",
    "Whether a site can be queried for 3PC transaction metrics.",
    ["site_id"],
)
ENROLLMENT_3PC_TRANSACTIONS = Gauge(
    "csdlpt_enrollment_3pc_transactions",
    "Current number of 3PC transaction records by site and state.",
    ["site_id", "state"],
)
ENROLLMENT_3PC_COLLECTION_FAILURES_TOTAL = Counter(
    "csdlpt_enrollment_3pc_collection_failures_total",
    "Number of failed attempts to collect 3PC transaction metrics from a site.",
    ["site_id"],
)


def observe_background_loop_failure(loop_name: str) -> None:
    BACKGROUND_LOOP_FAILURES_TOTAL.labels(loop=loop_name).inc()


def observe_course_read(
    *,
    endpoint: str,
    read_mode: str,
    source_site: str,
    served_site: str,
    duration_seconds: float,
    status: str,
) -> None:
    COURSE_READ_DURATION_SECONDS.labels(
        endpoint=endpoint,
        read_mode=read_mode,
        source_site=source_site,
        served_site=served_site,
    ).observe(duration_seconds)
    COURSE_READ_REQUESTS_TOTAL.labels(
        endpoint=endpoint,
        read_mode=read_mode,
        source_site=source_site,
        served_site=served_site,
        status=status,
    ).inc()


def observe_replication_summary(summary: dict[str, Any]) -> None:
    REPLICATION_RECOVERY_RUNS_TOTAL.inc()
    REPLICATION_RECOVERY_LAST_RUN_UNIX_SECONDS.set_to_current_time()
    REPLICATION_RECOVERY_LAST_BATCH.labels(result="attempted").set(summary.get("attempted", 0))
    REPLICATION_RECOVERY_LAST_BATCH.labels(result="delivered").set(summary.get("delivered", 0))
    REPLICATION_RECOVERY_LAST_BATCH.labels(result="pending").set(summary.get("pending", 0))
    REPLICATION_RECOVERY_LAST_BATCH.labels(result="failed").set(summary.get("failed", 0))

    for event in summary.get("events", []):
        REPLICATION_DISPATCH_EVENTS_TOTAL.labels(
            target_site=event.get("target_site", "UNKNOWN"),
            status=event.get("status", "UNKNOWN"),
        ).inc()

    refresh_replication_snapshot()


def observe_enrollment_recovery_summary(summary: dict[str, Any]) -> None:
    ENROLLMENT_3PC_RECOVERY_LAST_RUN_UNIX_SECONDS.set_to_current_time()
    recovered_commits = summary.get("recovered_commits", 0)
    recovered_aborts = summary.get("recovered_aborts", 0)
    ENROLLMENT_3PC_RECOVERY_LAST_BATCH.labels(result="committed").set(recovered_commits)
    ENROLLMENT_3PC_RECOVERY_LAST_BATCH.labels(result="aborted").set(recovered_aborts)
    ENROLLMENT_3PC_RECOVERY_TOTAL.labels(outcome="committed").inc(recovered_commits)
    ENROLLMENT_3PC_RECOVERY_TOTAL.labels(outcome="aborted").inc(recovered_aborts)

    refresh_3pc_snapshot()


def refresh_runtime_metrics() -> None:
    refresh_replication_snapshot()
    refresh_3pc_snapshot()


def refresh_replication_snapshot() -> None:
    from services.ReplicationService import ReplicationService

    status = ReplicationService.get_replication_status()
    outbox_counts = status.get("outbox", {}).get("counts", {})
    for outbox_status in REPLICATION_OUTBOX_STATUSES:
        REPLICATION_OUTBOX_EVENTS.labels(status=outbox_status).set(
            int(outbox_counts.get(outbox_status, 0))
        )

    for site in status.get("sites", []):
        site_id = site.get("site_id", "UNKNOWN")
        current_status = site.get("status", "UNKNOWN")
        current_role = site.get("role", "REPLICA")

        REPLICATION_SITE_UP.labels(site_id=site_id).set(1 if current_status == "ONLINE" else 0)
        for candidate_status in REPLICATION_SITE_STATUSES:
            REPLICATION_SITE_STATUS.labels(site_id=site_id, status=candidate_status).set(
                1 if current_status == candidate_status else 0
            )
        for candidate_role in REPLICATION_SITE_ROLES:
            REPLICATION_SITE_ROLE.labels(site_id=site_id, role=candidate_role).set(
                1 if current_role == candidate_role else 0
            )

        heartbeat = site.get("last_heartbeat")
        if heartbeat is None:
            REPLICATION_SITE_HEARTBEAT_AGE_SECONDS.labels(site_id=site_id).set(0)
        else:
            REPLICATION_SITE_HEARTBEAT_AGE_SECONDS.labels(site_id=site_id).set(
                max((_utc_now() - _normalize_datetime(heartbeat)).total_seconds(), 0)
            )


def refresh_3pc_snapshot() -> None:
    for site_id in SessionLocals:
        _reset_3pc_site_metrics(site_id)
        session = SessionLocals[site_id]()
        try:
            rows = (
                session.query(
                    EnrollmentTransaction.State,
                    func.count(EnrollmentTransaction.RecordId).label("count"),
                )
                .group_by(EnrollmentTransaction.State)
                .all()
            )
            ENROLLMENT_3PC_SITE_UP.labels(site_id=site_id).set(1)
            for state, count in rows:
                state_name = getattr(state, "value", str(state))
                ENROLLMENT_3PC_TRANSACTIONS.labels(site_id=site_id, state=state_name).set(int(count))
        except Exception:
            ENROLLMENT_3PC_SITE_UP.labels(site_id=site_id).set(0)
            ENROLLMENT_3PC_COLLECTION_FAILURES_TOTAL.labels(site_id=site_id).inc()
        finally:
            session.close()


def _reset_3pc_site_metrics(site_id: str) -> None:
    for state in ENROLLMENT_TRANSACTION_STATES:
        ENROLLMENT_3PC_TRANSACTIONS.labels(site_id=site_id, state=state).set(0)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
