# Quick Podman Image Size Check

Write-Host "`n🔍 Quick Podman Image Size Check`n" -ForegroundColor Cyan

# Kiểm tra Podman đã cài chưa
try {
    podman version | Out-Null
} catch {
    Write-Host "⚠ Podman is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "`nInstall Podman:" -ForegroundColor Yellow
    Write-Host "  - Download from: https://podman.io/getting-started/installation" -ForegroundColor Gray
    Write-Host "  - Or: choco install podman-desktop`n" -ForegroundColor Gray
    exit 1
}

# Kiểm tra có images không
$images = podman images smartfashion --format "{{.Repository}}:{{.Tag}}" 2>$null

if (-not $images) {
    Write-Host "⚠ No smartfashion images found!" -ForegroundColor Yellow
    Write-Host "`nBuild image first:" -ForegroundColor Gray
    Write-Host "  podman build -t smartfashion:latest ." -ForegroundColor White
    Write-Host "  or" -ForegroundColor Gray
    Write-Host "  podman-compose build`n" -ForegroundColor White
    exit 0
}

# Hiển thị images
Write-Host "📦 SmartFashion Images:`n" -ForegroundColor Green
podman images smartfashion --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.Created}}"

# Lấy image đầu tiên
$latestImage = podman images smartfashion --format "{{.Repository}}:{{.Tag}}" 2>$null | Select-Object -First 1

if ($latestImage) {
    # Hiển thị layer breakdown
    Write-Host "`n📊 Layer Breakdown for: $latestImage`n" -ForegroundColor Cyan
    podman history $latestImage --format "table {{.CreatedBy}}\t{{.Size}}" | Select-Object -First 15
    
    # Đếm layers
    $layerCount = (podman history $latestImage --quiet | Measure-Object -Line).Lines
    Write-Host "`n📈 Total Layers: $layerCount" -ForegroundColor Yellow
    
    # Get exact size
    $sizeBytes = podman inspect $latestImage --format='{{.Size}}' 2>$null
    if ($sizeBytes) {
        $sizeMB = [math]::Round($sizeBytes / 1MB, 2)
        $sizeGB = [math]::Round($sizeBytes / 1GB, 3)
        Write-Host "📏 Exact Size: $sizeMB MB ($sizeGB GB)" -ForegroundColor Yellow
    }
}

# Hiển thị disk usage
Write-Host "`n💾 Podman Disk Usage:`n" -ForegroundColor Cyan
podman system df

# Quick stats nếu có containers đang chạy
$runningContainers = podman ps --format "{{.Names}}" 2>$null
if ($runningContainers) {
    Write-Host "`n📊 Running Containers:`n" -ForegroundColor Cyan
    podman ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
}

Write-Host "`n💡 Quick Commands:" -ForegroundColor Yellow
Write-Host "  podman images -a                    # Show all images" -ForegroundColor Gray
Write-Host "  podman history smartfashion:latest  # View layer details" -ForegroundColor Gray
Write-Host "  podman system prune -a              # Clean unused images" -ForegroundColor Gray
Write-Host "  podman inspect smartfashion:latest  # Detailed info" -ForegroundColor Gray
Write-Host "  .\benchmark-podman.ps1              # Run benchmark`n" -ForegroundColor Gray
