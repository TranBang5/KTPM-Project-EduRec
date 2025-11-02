# PowerShell script to run Locust load tests

# Default values
param(
    [string]$Host = "http://api-gateway:5000",
    [int]$Users = 50,
    [int]$SpawnRate = 5,
    [string]$RunTime = "5m"
)

Write-Host "Starting Locust Load Test" -ForegroundColor Green
Write-Host "=========================================="
Write-Host "Host: $Host"
Write-Host "Users: $Users"
Write-Host "Spawn Rate: $SpawnRate users/second"
Write-Host "Run Time: $RunTime"
Write-Host "=========================================="

# Create reports directory if it doesn't exist
if (-not (Test-Path "reports")) {
    New-Item -ItemType Directory -Path "reports"
}

# Generate timestamp for report files
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = "reports\locust_${Timestamp}.html"
$CsvPrefix = "reports\locust_${Timestamp}"

# Run Locust test
docker compose run --rm locust locust `
  --host="$Host" `
  --users="$Users" `
  --spawn-rate="$SpawnRate" `
  --run-time="$RunTime" `
  --headless `
  --html="$ReportFile" `
  --csv="$CsvPrefix" `
  --loglevel=INFO

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green
Write-Host "Report: $ReportFile"
Write-Host "CSV files: ${CsvPrefix}_*.csv"

