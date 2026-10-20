#!/bin/bash
# ==============================================================================
# compare.sh - Docker Image Build & Size Benchmark
# ==============================================================================
set -e

echo "=========================================================="
echo " Docker Image Optimization Benchmark Report"
echo "=========================================================="

echo -e "\nInspecting Docker Images:"
docker images --filter "reference=image-optimizer*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true

echo -e "\nRunning Detailed Comparative Breakdown..."
python3 scripts/compare.py || python scripts/compare.py
