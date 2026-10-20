# ==============================================================================
# compare.ps1 - Windows PowerShell Docker Image Build & Size Benchmark
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Building Docker Images & Comparing Sizes" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Build Unoptimized Image
Write-Host "`n[1/3] Building Unoptimized Baseline Image (~1.5 GB)..." -ForegroundColor White
docker build -f Dockerfile.unoptimized -t image-optimizer:unoptimized .

# Step 2: Build Optimized Multi-Stage Image
Write-Host "`n[2/3] Building Optimized Multi-Stage Image (~140 MB)..." -ForegroundColor White
docker build -f Dockerfile -t image-optimizer:optimized .

# Step 3: Run 'docker images' comparison
Write-Host "`n[3/3] Inspecting Docker Images:" -ForegroundColor Green
docker images --filter "reference=image-optimizer*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Step 4: Python Benchmark Tool
Write-Host "`nRunning Detailed Comparative Breakdown..." -ForegroundColor Cyan
python scripts/compare.py

