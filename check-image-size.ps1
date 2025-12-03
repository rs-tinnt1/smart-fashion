# Quick Docker Image Size Check

Write-Host "`n🔍 Quick Docker Image Size Check`n" -ForegroundColor Cyan

# Kiểm tra có images không
$images = docker images smartfashion:* --format "{{.Repository}}:{{.Tag}}" 2>$null

if (-not $images) {
    Write-Host "⚠ No smartfashion images found!" -ForegroundColor Yellow
    Write-Host "`nBuild images first:" -ForegroundColor Gray
    Write-Host "  docker build -t smartfashion:latest ." -ForegroundColor White
    exit 0
}

# Hiển thị images
Write-Host "📦 SmartFashion Images:`n" -ForegroundColor Green
docker images smartfashion:* --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"

# Hiển thị history của image đầu tiên
$latestImage = docker images smartfashion --format "{{.Repository}}:{{.Tag}}" 2>$null | Select-Object -First 1

if ($latestImage) {
    Write-Host "`n📊 Layer Breakdown for: $latestImage`n" -ForegroundColor Cyan
    docker history $latestImage --human=true --format "table {{.CreatedBy}}\t{{.Size}}"
}

# Tổng kết disk usage
Write-Host "`n💾 Docker Disk Usage:`n" -ForegroundColor Cyan
docker system df

Write-Host "`n💡 Quick Commands:" -ForegroundColor Yellow
Write-Host "  docker images -a              # Show all images" -ForegroundColor Gray
Write-Host "  docker system prune -a        # Clean unused images" -ForegroundColor Gray
Write-Host "  dive smartfashion:latest      # Analyze layers" -ForegroundColor Gray
Write-Host "  docker inspect smartfashion   # Detailed info`n" -ForegroundColor Gray
