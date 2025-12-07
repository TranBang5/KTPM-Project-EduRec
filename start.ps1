# PowerShell script to start the microservices system
# Usage: .\start.ps1 [service_name]

Write-Host "🚀 Starting Student Study Plan Recommendation System..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Start services
if ($args.Count -eq 0) {
    Write-Host "📦 Starting all services..." -ForegroundColor Cyan
    docker-compose up -d --build
} else {
    Write-Host "📦 Starting service: $($args[0])" -ForegroundColor Cyan
    docker-compose up -d --build $args[0]
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check health
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "⚠️  API Gateway not ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "  docker-compose ps          # Check status"
Write-Host "  docker-compose logs -f     # View logs"
Write-Host "  docker-compose down        # Stop services"
Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:8080"
Write-Host "  API Gateway: http://localhost:5000"
Write-Host "  Health Check: http://localhost:5000/health"
