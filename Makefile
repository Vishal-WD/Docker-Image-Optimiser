.PHONY: help build-all build-opt build-unopt run compare test clean

help:
	@echo "Docker Image Optimizer - Available Commands:"
	@echo "  make build-all    - Build both unoptimized and optimized Docker images"
	@echo "  make build-opt    - Build only the multi-stage optimized image"
	@echo "  make build-unopt  - Build the unoptimized baseline image"
	@echo "  make compare      - Compare image sizes using docker images and benchmark tool"
	@echo "  make run          - Launch the full stack (FastAPI + PostgreSQL) with docker compose"
	@echo "  make test         - Run pytest test suite"
	@echo "  make clean        - Stop containers and remove built test images"

build-all: build-unopt build-opt

build-unopt:
	docker build -f Dockerfile.unoptimized -t image-optimizer:unoptimized .

build-opt:
	docker build -f Dockerfile -t image-optimizer:optimized .

compare:
	docker images --filter "reference=image-optimizer*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
	python scripts/compare.py

run:
	docker compose up --build

test:
	pytest -v tests/

clean:
	docker compose down -v
	docker rmi image-optimizer:optimized image-optimizer:unoptimized || true

