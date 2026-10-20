#!/bin/bash
# ==============================================================================
# compare.sh - Docker Image Build & Size Benchmark
# ==============================================================================
set -e

echo "=========================================================="
echo " Building Docker Images & Comparing Sizes"
echo "=========================================================="

echo -e "\n[1/3] Building Unoptimized Baseline Image (~1.5 GB)..."
docker build -f Dockerfile.unoptimized -t image-optimizer:unoptimized .

echo -e "\n[2/3] Building Optimized Multi-Stage Image (~140 MB)..."
docker build -f Dockerfile -t image-optimizer:optimized .

echo -e "\n[3/3] Inspecting Docker Images:"
docker images --filter "reference=image-optimizer*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo -e "\nRunning Detailed Comparative Breakdown..."
python3 scripts/compare.py

