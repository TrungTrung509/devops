import asyncio
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

import models
from configs.db import Base, engines
from configs.seed import seed_all
from exceptions import register_exception_handlers
from monitoring.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
    observe_background_loop_failure,
    observe_enrollment_recovery_summary,
    observe_replication_summary,
    refresh_runtime_metrics,
)
from routers import auth, branch, class_section, classroom, course, department, teacher, schedule, semester, student_management, user, enrollment, failover
from services.Enrollment3PCService import Enrollment3PCService
from services.ReplicationService import ReplicationService
from services.KafkaQueueService import KafkaQueueService
from services.KafkaWorkerService import KafkaWorkerService


REPLICATION_RECOVERY_INTERVAL_SECONDS = 10
ENROLLMENT_3PC_RECOVERY_INTERVAL_SECONDS = 10

from fastapi.middleware.cors import CORSMiddleware
from routers import auth, branch, class_section, classroom, course, department, teacher, schedule, semester, student_management, user, enrollment, report

for branch_id, engine in engines.items():
    print(f"Initializing database for site: {branch_id}")
    Base.metadata.create_all(bind=engine)

seed_all()
print("All tables created and default data seeded successfully!")


async def replication_recovery_loop():
    while True:
        try:
            summary = await asyncio.to_thread(ReplicationService.dispatch_outbox_events)
            observe_replication_summary(summary)
            if summary.get("attempted", 0):
                print(
                    "Replication auto recovery: "
                    f"attempted={summary['attempted']}, "
                    f"delivered={summary['delivered']}, "
                    f"pending={summary['pending']}, "
                    f"failed={summary['failed']}"
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            observe_background_loop_failure("replication")
            print(f"Replication auto recovery failed: {exc}")

        await asyncio.sleep(REPLICATION_RECOVERY_INTERVAL_SECONDS)


async def enrollment_3pc_recovery_loop():
    while True:
        try:
            summary = await asyncio.to_thread(Enrollment3PCService.recover_in_doubt_transactions)
            observe_enrollment_recovery_summary(summary)
            if summary.get("recovered_commits", 0) or summary.get("recovered_aborts", 0):
                print(
                    "Enrollment 3PC recovery: "
                    f"committed={summary['recovered_commits']}, "
                    f"aborted={summary['recovered_aborts']}"
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            observe_background_loop_failure("enrollment_3pc")
            print(f"Enrollment 3PC recovery failed: {exc}")

        await asyncio.sleep(ENROLLMENT_3PC_RECOVERY_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        refresh_runtime_metrics()
    except Exception as exc:
        print(f"Initial metrics refresh failed: {exc}")

    # Start Kafka Services
    try:
        await KafkaQueueService.start()
        await KafkaWorkerService.start()
    except Exception as exc:
        print(f"Warning: Failed to start Kafka services (Kafka broker might be offline): {exc}")

    recovery_task = asyncio.create_task(replication_recovery_loop())
    enrollment_3pc_task = asyncio.create_task(enrollment_3pc_recovery_loop())
    try:
        yield
    finally:
        recovery_task.cancel()
        enrollment_3pc_task.cancel()
        with suppress(asyncio.CancelledError):
            await recovery_task
        with suppress(asyncio.CancelledError):
            await enrollment_3pc_task

        # Stop Kafka Services
        try:
            await KafkaQueueService.stop()
            await KafkaWorkerService.stop()
        except Exception as exc:
            print(f"Failed to stop Kafka services: {exc}")


app = FastAPI(
    title="BTL-CSDLPT API",
    description="API for Distributed Database - Branch Registration System",
    version="1.1.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)


def _metric_path(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path or request.url.path


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    path = _metric_path(request)
    if path == "/metrics":
        return await call_next(request)

    method = request.method
    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - started_at
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status="500").inc()
        raise
    finally:
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

    duration = time.perf_counter() - started_at
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status=str(response.status_code),
    ).inc()
    return response

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(branch.router)
app.include_router(department.router)
app.include_router(course.router)
app.include_router(semester.router)
app.include_router(class_section.router)
app.include_router(classroom.router)
app.include_router(schedule.router)
app.include_router(student_management.router)
app.include_router(teacher.router)
app.include_router(enrollment.router)
app.include_router(failover.router)
app.include_router(report.router)


@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "message": "Welcome to BTL-CSDLPT API",
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    from schemas.api_response import success_response

    return success_response(
        data={"status": "healthy", "version": "1.1.1"},
        message="He thong dang hoat dong",
        status=200,
    )


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
