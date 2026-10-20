from contextlib import asynccontextmanager
import base64
import io
import time
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from PIL import Image

from app.config import settings
from app.database import engine, get_db, init_db, active_db_type
from app.models import ImageOptimization


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Python Docker footprint optimization demo with PostgreSQL persistence.",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the interactive web frontend dashboard."""
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


@app.get("/api/docker/metrics")
def get_docker_metrics():
    """Returns image size benchmarks, savings percentages, and layer statistics."""
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


@app.post("/api/optimize-image")
async def optimize_media_image(
    file: UploadFile = File(...),
    quality: int = Form(80),
    format: str = Form("WEBP"),
    db: Session = Depends(get_db)
):
    """
    Compresses an uploaded JPEG/PNG image using Pillow (native C-libraries),
    stores the optimization metrics into PostgreSQL, and returns the result.
    """
    try:
        contents = await file.read()
        orig_size_bytes = len(contents)
        if orig_size_bytes == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        # Open image with Pillow
        img = Image.open(io.BytesIO(contents))

        # Convert RGBA to RGB if saving to JPEG
        format_upper = format.upper()
        if format_upper == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Compress to output buffer
        out_buf = io.BytesIO()
        save_kwargs = {"quality": quality, "optimize": True}
        if format_upper == "WEBP":
            img.save(out_buf, format="WEBP", quality=quality, method=6)
        elif format_upper == "JPEG":
            img.save(out_buf, format="JPEG", **save_kwargs)
        elif format_upper == "PNG":
            img.save(out_buf, format="PNG", optimize=True)
        else:
            img.save(out_buf, format=format_upper, **save_kwargs)

        opt_bytes = out_buf.getvalue()
        opt_size_bytes = len(opt_bytes)

        orig_kb = orig_size_bytes / 1024.0
        opt_kb = opt_size_bytes / 1024.0
        saved_kb = max(0.0, orig_kb - opt_kb)
        reduction = max(0.0, round(((orig_kb - opt_kb) / orig_kb) * 100, 2)) if orig_kb > 0 else 0.0

        # Persist log in PostgreSQL
        record = ImageOptimization(
            filename=file.filename or "uploaded_image",
            original_size_kb=orig_kb,
            optimized_size_kb=opt_kb,
            saved_bytes_kb=saved_kb,
            reduction_percent=reduction,
            format=format_upper
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Return Base64 encoded result for direct browser rendering
        encoded_img = base64.b64encode(opt_bytes).decode("utf-8")

        return {
            "id": record.id,
            "filename": record.filename,
            "original_size_kb": round(orig_kb, 2),
            "optimized_size_kb": round(opt_kb, 2),
            "saved_bytes_kb": round(saved_kb, 2),
            "reduction_percent": reduction,
            "format": format_upper,
            "optimized_base64": encoded_img
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image compression failed: {str(e)}")


@app.get("/api/optimizations")
def list_optimizations(db: Session = Depends(get_db)):
    """Returns recent image optimization records stored in PostgreSQL."""
    records = db.query(ImageOptimization).order_by(ImageOptimization.id.desc()).limit(50).all()
    return [r.to_dict() for r in records]
