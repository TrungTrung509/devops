from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
import os

CNTT_URL = os.environ.get("CNTT_URL", "postgresql://bench_user:bench_password@postgres_cntt:5432/db_cntt")
CB_URL = os.environ.get("CB_URL", "postgresql://bench_user:bench_password@postgres_cb:5432/db_cb")
NN_URL = os.environ.get("NN_URL", "postgresql://bench_user:bench_password@postgres_nn:5432/db_nn")
KT_URL = os.environ.get("KT_URL", "postgresql://bench_user:bench_password@postgres_kt:5432/db_kt")
DT_URL = os.environ.get("DT_URL", "postgresql://bench_user:bench_password@postgres_dt:5432/db_dt")

ENGINE_KWARGS = {"pool_pre_ping": True, "pool_size": 20, "max_overflow": 10}

engines = {
    "CNTT": create_engine(CNTT_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "CB": create_engine(CB_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "NN": create_engine(NN_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "KT": create_engine(KT_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "DT": create_engine(DT_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
}

SessionLocals = {
    site: sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    for site, engine in engines.items()
}

Base = declarative_base()

def open_db_by_branch(branch_id: str) -> Session:
    branch_id = (branch_id or "").upper()
    if branch_id not in SessionLocals:
        raise HTTPException(status_code=400, detail="Mã khoa không hợp lệ")
    return SessionLocals[branch_id]()
