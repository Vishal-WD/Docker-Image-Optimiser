import io
import os
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is created before tests run."""
    init_db()


def test_healthcheck():
    """Verify application health and database connection."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "database_type" in data


def test_docker_metrics():
    """Verify Docker benchmark metrics endpoint returns correct baseline data."""
    response = client.get("/api/docker/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["unoptimized_size_mb"] == 1520.0
    assert data["optimized_size_mb"] == 142.0
    assert data["reduction_percentage"] > 90.0
    assert len(data["breakdown"]) > 0


def test_media_image_optimization():
    """Test image compression and PostgreSQL record insertion."""
    # Generate a dummy RGB image in memory
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("test_sample.jpg", buf, "image/jpeg")}
    data = {"quality": 75, "format": "WEBP"}

    response = client.post("/api/optimize-image", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["filename"] == "test_sample.jpg"
    assert res_data["format"] == "WEBP"
    assert res_data["optimized_size_kb"] > 0
    assert "optimized_base64" in res_data

    # Verify record was stored in database
    history_res = client.get("/api/optimizations")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert any(h["filename"] == "test_sample.jpg" for h in history)


def test_dockerfile_best_practices():
    """Validate Dockerfile adheres to the required assignment optimizations."""
    dockerfile_path = "Dockerfile"
    assert os.path.exists(dockerfile_path), "Production Dockerfile must exist"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Slim base image
    assert "slim" in content, "Must use a slim base image"
    # 2. Multi-stage build
    assert "AS builder" in content, "Must have a builder stage"
    assert "AS runtime" in content, "Must have a runtime stage"
    # 3. Non-root user
    assert "USER appuser" in content or "USER 10001" in content, "Must drop privileges to non-root user"
    # 4. Pip cache pruning
    assert "--no-cache-dir" in content, "Must use --no-cache-dir for pip installs"


def test_dockerignore_rules():
    """Verify that .dockerignore exists and excludes key bloat files."""
    assert os.path.exists(".dockerignore"), ".dockerignore must exist"
    with open(".dockerignore", "r", encoding="utf-8") as f:
        rules = f.read()

    assert ".git" in rules, ".git must be ignored"
    assert "__pycache__" in rules, "python cache must be ignored"
    assert "tests/" in rules or "tests" in rules, "tests must be excluded from production image"
