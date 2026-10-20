from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Depends, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.database import engine, get_db, init_db, active_db_type
from app.models import DockerOptimizationRecord
from app.optimizer import (
    analyze_dockerfile,
    generate_optimized_dockerfile,
    DEFAULT_UNOPTIMIZED_DOCKERFILE,
    STANDARD_DOCKERIGNORE
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Python Docker footprint optimization suite with PostgreSQL persistence.",
    lifespan=lifespan
)


class DockerOptimizeRequest(BaseModel):
    dockerfile: str
    project_name: Optional[str] = "python-app"
    python_version: Optional[str] = "3.11"


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the interactive Docker Image Optimizer web dashboard."""
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error loading index.html: {str(e)}</h1>",
            status_code=500
        )


@app.get("/health")
def healthcheck(db: Session = Depends(get_db)):
    """Healthcheck endpoint for Docker HEALTHCHECK and monitoring."""
    db_status = "healthy"
    latency_ms = None
    try:
        t0 = time.time()
        db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - t0) * 1000, 2)
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "database_type": active_db_type,
        "database_latency_ms": latency_ms,
    }


@app.get("/api/default-dockerfile")
def get_default_dockerfile():
    """Returns the baseline unoptimized 1.5 GB Dockerfile for testing."""
    return {
        "dockerfile": DEFAULT_UNOPTIMIZED_DOCKERFILE,
        "standard_dockerignore": STANDARD_DOCKERIGNORE
    }


@app.post("/api/optimize-dockerfile")
def optimize_dockerfile_endpoint(
    payload: DockerOptimizeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyzes an unoptimized Dockerfile, detects bloat antipatterns,
    generates a production-grade multi-stage Dockerfile + .dockerignore,
    persists the audit log in PostgreSQL, and returns the comparative metrics.
    """
    raw_dockerfile = payload.dockerfile.strip()
    if not raw_dockerfile:
        raise HTTPException(status_code=400, detail="Dockerfile content cannot be empty.")

    # 1. Run static analysis & size estimation
    analysis = analyze_dockerfile(raw_dockerfile)

    # 2. Generate optimized multi-stage Dockerfile
    optimized_df = generate_optimized_dockerfile(raw_dockerfile, payload.python_version or "3.11")

    # 3. Generate matching .dockerignore
    dockerignore = STANDARD_DOCKERIGNORE

    # 4. Save audit record into PostgreSQL
    try:
        record = DockerOptimizationRecord(
            project_name=payload.project_name or "python-app",
            original_dockerfile=raw_dockerfile,
            optimized_dockerfile=optimized_df,
            dockerignore_content=dockerignore,
            original_size_mb=analysis["estimated_original_mb"],
            optimized_size_mb=analysis["estimated_optimized_mb"],
            saved_mb=analysis["saved_mb"],
            reduction_percent=analysis["reduction_percentage"],
            issues_found_count=analysis["issue_count"]
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id
    except Exception as e:
        record_id = None

    return {
        "id": record_id,
        "project_name": payload.project_name,
        "analysis": analysis,
        "optimized_dockerfile": optimized_df,
        "dockerignore_content": dockerignore,
        "persisted_in_db": record_id is not None
    }


@app.get("/api/docker/metrics")
def get_docker_metrics():
    """Returns baseline image size benchmarks, savings percentages, and layer statistics."""
    unoptimized = settings.UNOPTIMIZED_SIZE_MB
    optimized = settings.OPTIMIZED_SIZE_MB
    saved = round(unoptimized - optimized, 1)
    reduction = round(((unoptimized - optimized) / unoptimized) * 100, 1)

    return {
        "unoptimized_size_mb": unoptimized,
        "optimized_size_mb": optimized,
        "saved_size_mb": saved,
        "reduction_percentage": reduction,
        "layer_count_unoptimized": 19,
        "layer_count_optimized": 7,
        "breakdown": [
            {"component": "Base OS (Debian vs Slim Bookworm)", "saved_mb": 880.0},
            {"component": "Compilers & Build Headers (gcc, g++, make)", "saved_mb": 260.0},
            {"component": "Pip & Apt Caches (Enforced --no-cache-dir)", "saved_mb": 120.0},
            {"component": "Dev Dependencies (pytest, black, mypy)", "saved_mb": 70.0},
            {"component": "Build Context Filtering (.dockerignore)", "saved_mb": 48.0},
        ],
        "security": {
            "cve_unoptimized": 184,
            "cve_optimized": 12,
            "non_root_user": True,
            "user_id": 10001
        }
    }


@app.get("/api/optimizations")
def list_optimizations(db: Session = Depends(get_db)):
    """Returns recent Docker optimization audits stored in PostgreSQL."""
    records = db.query(DockerOptimizationRecord).order_by(DockerOptimizationRecord.id.desc()).limit(50).all()
    return [r.to_dict() for r in records]
