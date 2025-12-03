# ========================================
# Docker Build Optimization Benchmark
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Docker Build Optimization Benchmark  " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Kiểm tra Docker đã chạy chưa
try {
    docker version | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    exit 1
}

# Enable BuildKit for faster builds
$env:DOCKER_BUILDKIT = 1

# Cleanup trước khi build
Write-Host "[0/3] Cleaning up old images..." -ForegroundColor Magenta
docker rmi -f smartfashion:original smartfashion:optimized 2>$null

# Build 1: Original Dockerfile
Write-Host "`n[1/2] Building Original Dockerfile..." -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
$time1 = Measure-Command {
    docker build -t smartfashion:original -f Dockerfile . 2>&1 | Out-Host
}
if ($LASTEXITCODE -eq 0) {
    $size1 = docker images smartfashion:original --format "{{.Size}}"
    Write-Host "✓ Build successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    $size1 = "N/A"
}

# Build 2: Optimized Multi-Stage
Write-Host "`n[2/2] Building Optimized Multi-Stage Dockerfile..." -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
$time2 = Measure-Command {
    docker build -t smartfashion:optimized -f Dockerfile.optimized . 2>&1 | Out-Host
}
if ($LASTEXITCODE -eq 0) {
    $size2 = docker images smartfashion:optimized --format "{{.Size}}"
    Write-Host "✓ Build successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    $size2 = "N/A"
}

# Results Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  BENCHMARK RESULTS                    " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Original
Write-Host "📦 Original Dockerfile:" -ForegroundColor White
Write-Host "   Build Time: $([math]::Round($time1.TotalSeconds, 2))s" -ForegroundColor Gray
Write-Host "   Image Size: $size1" -ForegroundColor Gray

# Optimized
Write-Host "`n📦 Optimized Multi-Stage:" -ForegroundColor White
Write-Host "   Build Time: $([math]::Round($time2.TotalSeconds, 2))s" -ForegroundColor Gray
Write-Host "   Image Size: $size2" -ForegroundColor Gray

# Calculate improvements
if ($size1 -ne "N/A" -and $size2 -ne "N/A") {
    $timeSaved = $time1.TotalSeconds - $time2.TotalSeconds
    $timeImprovement = [math]::Round(($timeSaved / $time1.TotalSeconds) * 100, 2)
    
    Write-Host "`n📊 Improvements:" -ForegroundColor Cyan
    if ($timeSaved -gt 0) {
        Write-Host "   ✓ Build Time: -$timeImprovement% faster" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Build Time: $([math]::Abs($timeImprovement))% slower (expected for first build)" -ForegroundColor Yellow
    }
}

# Image Details
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  IMAGE DETAILS                        " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

docker images smartfashion:* --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Layer Analysis
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LAYER ANALYSIS (Optimized)           " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

docker history smartfashion:optimized --human=true --no-trunc=false | Select-Object -First 10

Write-Host "`n💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Use 'dive smartfashion:optimized' for detailed layer analysis" -ForegroundColor Gray
Write-Host "   - Run 'docker system df' to see overall Docker disk usage" -ForegroundColor Gray
Write-Host "   - Run 'docker system prune -a' to clean up unused images" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
