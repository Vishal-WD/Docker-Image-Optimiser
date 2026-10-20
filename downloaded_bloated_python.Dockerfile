# ==============================================================================
# DOWNLOADED FROM WEB: Unoptimized Python Web Service Pattern
# Common tutorial baseline (> 1.4 GB image footprint)
# ==============================================================================

FROM python:3.11

ENV PYTHONUNBUFFERED=1

# Installs heavy build tools and dependencies without cleaning up apt cache
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libpq-dev

WORKDIR /app

# Copies entire project context (including .git, tests, and temporary files)
COPY . /app

# Preserves pip download caches in layer
RUN pip install -r requirements-dev.txt

# Runs as root user (security anti-pattern)
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
