import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db
from app.optimizer import DEFAULT_UNOPTIMIZED_DOCKERFILE

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


def test_dockerfile_optimization_pipeline():
    """Test Dockerfile static analysis, multi-stage generation, and PostgreSQL persistence."""
    payload = {
        "dockerfile": DEFAULT_UNOPTIMIZED_DOCKERFILE,
        "project_name": "python-fastapi-service",
        "python_version": "3.11"
    }

    response = client.post("/api/optimize-dockerfile", json=payload)
    assert response.status_code == 200
    res_data = response.json()

    # 1. Verify static analysis detected bloat
    analysis = res_data["analysis"]
    assert analysis["estimated_original_mb"] >= 1500.0
    assert analysis["estimated_optimized_mb"] <= 150.0
    assert analysis["reduction_percentage"] > 90.0
    assert analysis["issue_count"] >= 5

    # 2. Verify generated multi-stage Dockerfile
    opt_df = res_data["optimized_dockerfile"]
    assert "AS builder" in opt_df
    assert "AS runtime" in opt_df
    assert "python:3.11-slim" in opt_df
    assert "--no-cache-dir" in opt_df
    assert "USER appuser" in opt_df
    assert "HEALTHCHECK" in opt_df

    # 3. Verify generated .dockerignore
    assert ".git" in res_data["dockerignore_content"]
    assert "__pycache__" in res_data["dockerignore_content"]

    # 4. Verify PostgreSQL persistence
    history_res = client.get("/api/optimizations")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert any(h["project_name"] == "python-fastapi-service" for h in history)


def test_default_dockerfile_endpoint():
    """Verify default Dockerfile endpoint returns unoptimized baseline."""
    response = client.get("/api/default-dockerfile")
    assert response.status_code == 200
    data = response.json()
    assert "FROM python:3.11" in data["dockerfile"]
    assert ".git" in data["standard_dockerignore"]


def test_download_dockerignore():
    """Verify dockerignore download returns 'dockerignore.txt' with text/plain."""
    payload = {"dockerfile": "FROM python:3.11", "dockerignore": ".git\n__pycache__/"}
    response = client.post("/api/download/dockerignore", json=payload)
    assert response.status_code == 200
    assert 'filename="dockerignore.txt"' in response.headers.get("Content-Disposition", "")
    assert "text/plain" in response.headers.get("Content-Type")
    assert ".git" in response.text


def test_download_bundle():
    """Verify Docker bundle download returns a valid zip."""
    payload = {"dockerfile": "FROM python:3.11-slim\nCMD ['python']"}
    response = client.post("/api/download/docker-bundle", json=payload)
    assert response.status_code == 200
    assert len(response.content) > 100


def test_download_docker_image_tar():
    """Verify Docker image tar download returns a spec-compliant tar archive with manifest, repositories, VERSION, and layer.tar."""
    import tarfile, io, json
    response = client.post("/api/download/docker-image-tar")
    assert response.status_code == 200
    assert "application/x-tar" in response.headers.get("Content-Type")
    assert 'filename="image-optimizer-optimized.tar"' in response.headers.get("Content-Disposition")

    # Verify tar content integrity
    tf = tarfile.open(fileobj=io.BytesIO(response.content))
    names = tf.getnames()
    assert "repositories" in names, "Archive must contain repositories JSON"
    assert "manifest.json" in names, "Archive must contain manifest.json"

    # Verify VERSION files and layer.tar files
    version_files = [n for n in names if n.endswith("/VERSION")]
    layer_tars = [n for n in names if n.endswith("/layer.tar")]
    assert len(version_files) >= 1, "Must contain at least one VERSION file"
    assert len(layer_tars) >= 1, "Must contain at least one layer.tar filesystem archive"

    for vf in version_files:
        assert b"1.0" in tf.extractfile(vf).read()


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
