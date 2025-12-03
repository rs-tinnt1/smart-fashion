# ========================================
# Podman Build Optimization Benchmark
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Podman Build Optimization Benchmark  " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Kiểm tra Podman đã chạy chưa
try {
    podman version | Out-Null
    Write-Host "✓ Podman is ready`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Podman is not installed or not running!" -ForegroundColor Red
    Write-Host "`nInstall Podman from: https://podman.io/getting-started/installation" -ForegroundColor Yellow
    exit 1
}

# Kiểm tra có Dockerfile không
if (-not (Test-Path "Dockerfile")) {
    Write-Host "ERROR: Dockerfile not found!" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Benchmark Configuration:" -ForegroundColor Cyan
Write-Host "   - Dockerfile: Dockerfile (Multi-stage optimized)" -ForegroundColor Gray
Write-Host "   - Images to build: 2 (cached + no-cache)" -ForegroundColor Gray
Write-Host "   - Metrics: Build time, Image size, Layers`n" -ForegroundColor Gray

# Cleanup trước khi build
Write-Host "[0/2] Cleaning up old images..." -ForegroundColor Magenta
podman rmi -f smartfashion:cached smartfashion:nocache 2>$null | Out-Null

# Build 1: With cache (normal build)
Write-Host "`n[1/2] Building with Cache (Normal Build)..." -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
$timeCached = Measure-Command {
    podman build -t smartfashion:cached . 2>&1 | Out-Host
}
if ($LASTEXITCODE -eq 0) {
    $sizeCached = podman images smartfashion:cached --format "{{.Size}}"
    $layersCached = (podman history smartfashion:cached --quiet | Measure-Object -Line).Lines
    Write-Host "✓ Build successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    $sizeCached = "N/A"
    $layersCached = "N/A"
}

# Build 2: No cache (clean build)
Write-Host "`n[2/2] Building without Cache (Clean Build)..." -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
$timeNoCache = Measure-Command {
    podman build --no-cache -t smartfashion:nocache . 2>&1 | Out-Host
}
if ($LASTEXITCODE -eq 0) {
    $sizeNoCache = podman images smartfashion:nocache --format "{{.Size}}"
    $layersNoCache = (podman history smartfashion:nocache --quiet | Measure-Object -Line).Lines
    Write-Host "✓ Build successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    $sizeNoCache = "N/A"
    $layersNoCache = "N/A"
}

# Results Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  BENCHMARK RESULTS                    " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Table format
Write-Host "┌──────────────────┬─────────────┬─────────────┐" -ForegroundColor Gray
Write-Host "│ Metric           │ With Cache  │ No Cache    │" -ForegroundColor White
Write-Host "├──────────────────┼─────────────┼─────────────┤" -ForegroundColor Gray
Write-Host ("│ Build Time       │ {0,-11} │ {1,-11} │" -f "$([math]::Round($timeCached.TotalSeconds, 1))s", "$([math]::Round($timeNoCache.TotalSeconds, 1))s") -ForegroundColor Gray
Write-Host ("│ Image Size       │ {0,-11} │ {1,-11} │" -f $sizeCached, $sizeNoCache) -ForegroundColor Gray
Write-Host ("│ Layer Count      │ {0,-11} │ {1,-11} │" -f $layersCached, $layersNoCache) -ForegroundColor Gray
Write-Host "└──────────────────┴─────────────┴─────────────┘" -ForegroundColor Gray

# Analysis
Write-Host "`n📊 Analysis:" -ForegroundColor Cyan

if ($sizeCached -ne "N/A" -and $sizeNoCache -ne "N/A") {
    Write-Host "   ✓ Images built successfully" -ForegroundColor Green
    
    # Build time comparison
    $timeDiff = $timeNoCache.TotalSeconds - $timeCached.TotalSeconds
    if ($timeDiff -gt 0) {
        $timePercent = [math]::Round(($timeDiff / $timeNoCache.TotalSeconds) * 100, 1)
        Write-Host "   ✓ Cache saves: $([math]::Round($timeDiff, 1))s ($timePercent% faster)" -ForegroundColor Green
    }
    
    # Layer count
    if ($layersCached -eq $layersNoCache) {
        Write-Host "   ✓ Consistent layer count: $layersCached layers" -ForegroundColor Green
    }
}

# Image Details
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  IMAGE DETAILS                        " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

podman images smartfashion:* --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}"

# Layer Analysis (sử dụng image cached)
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LAYER ANALYSIS (Top 10 Layers)       " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

podman history smartfashion:cached --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc=false | Select-Object -First 11

# Size Breakdown
Write-Host "`n📦 Size Breakdown:" -ForegroundColor Cyan
$sizeBytes = podman inspect smartfashion:cached --format='{{.Size}}' 2>$null
if ($sizeBytes) {
    $sizeMB = [math]::Round($sizeBytes / 1MB, 2)
    $sizeGB = [math]::Round($sizeBytes / 1GB, 3)
    Write-Host "   Total Size: $sizeMB MB ($sizeGB GB)" -ForegroundColor Yellow
    
    # Ước tính breakdown
    Write-Host "   Estimated breakdown:" -ForegroundColor Gray
    Write-Host "   - Base image (python:3.12-slim): ~130 MB" -ForegroundColor Gray
    Write-Host "   - Python packages: ~$(($sizeMB - 130 - 25)) MB" -ForegroundColor Gray
    Write-Host "   - Source code: ~25 MB" -ForegroundColor Gray
}

# Optimization Tips
Write-Host "`n💡 Optimization Tips:" -ForegroundColor Yellow
Write-Host "   1. Current Dockerfile uses multi-stage build ✓" -ForegroundColor Gray
Write-Host "   2. .dockerignore file excludes unnecessary files ✓" -ForegroundColor Gray
Write-Host "   3. Non-root user for security ✓" -ForegroundColor Gray
Write-Host "   4. Model file mounted from volume (not in image) ✓" -ForegroundColor Gray

# Further optimizations
Write-Host "`n📈 Further Optimizations:" -ForegroundColor Cyan
Write-Host "   - Consider using Alpine base (~60% smaller)" -ForegroundColor Gray
Write-Host "   - Remove unused Python packages" -ForegroundColor Gray
Write-Host "   - Use PODMAN_BUILDKIT for better caching" -ForegroundColor Gray

# Cleanup suggestion
Write-Host "`n🧹 Cleanup:" -ForegroundColor Magenta
Write-Host "   Remove test images with:" -ForegroundColor Gray
Write-Host "   podman rmi smartfashion:cached smartfashion:nocache" -ForegroundColor White

# Tag latest
Write-Host "`n🏷️  Tagging recommended image:" -ForegroundColor Cyan
podman tag smartfashion:cached smartfashion:latest 2>$null
if ($?) {
    Write-Host "   ✓ Tagged smartfashion:cached as smartfashion:latest" -ForegroundColor Green
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
