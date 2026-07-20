import time
import os
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry, multiprocess
from monitoring.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION
from services.SimpleEnrollmentService import SimpleEnrollmentService

app = FastAPI(title="Benchmark Khoa API")

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    path = request.url.path
    start_time = time.perf_counter()
    status_code = "500"

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    except Exception:
        status_code = "500"
        raise
    finally:
        latency = time.perf_counter() - start_time
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status_code, app="khoa").inc()
        HTTP_REQUEST_DURATION.labels(method=method, path=path, app="khoa").observe(latency)

@app.get("/metrics", include_in_schema=False)
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

class EnrollmentCreate(BaseModel):
    userId: str
    MaLopHP: str

class CancelRequest(BaseModel):
    userId: str
    MaLopHP: str

@app.post("/enrollments/register-bench", status_code=201)
def register_bench(body: EnrollmentCreate):
    """Đăng ký hoặc Đổi lớp (tự động phát hiện nếu đã đăng ký cùng MaHP)."""
    return SimpleEnrollmentService.register_simple(
        user_id=body.userId,
        ma_lop_hp=body.MaLopHP
    )

@app.delete("/enrollments/cancel-bench")
def cancel_bench(body: CancelRequest):
    """Hủy đăng ký học phần."""
    return SimpleEnrollmentService.cancel_simple(
        user_id=body.userId,
        ma_lop_hp=body.MaLopHP
    )
