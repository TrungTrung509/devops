from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
import os

HD_URL = os.environ.get("HD_URL", "postgresql://bench_user:bench_password@postgres_hd:5432/db_hd")
HL_URL = os.environ.get("HL_URL", "postgresql://bench_user:bench_password@postgres_hl:5432/db_hl")
NT_URL = os.environ.get("NT_URL", "postgresql://bench_user:bench_password@postgres_nt:5432/db_nt")

ENGINE_KWARGS = {"pool_pre_ping": True, "pool_size": 20, "max_overflow": 10}

engines = {
    "HD": create_engine(HD_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "HL": create_engine(HL_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
    "NT": create_engine(NT_URL, connect_args={"connect_timeout": 5}, **ENGINE_KWARGS),
}

SessionLocals = {
    site: sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    for site, engine in engines.items()
}

Base = declarative_base()

def open_db_by_branch(branch_id: str) -> Session:
    branch_id = (branch_id or "").upper()
    if branch_id not in SessionLocals:
        raise HTTPException(status_code=400, detail="Mã cơ sở không hợp lệ")
    return SessionLocals[branch_id]()
