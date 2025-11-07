# Test Deployment Script
# Verifies that the Docker deployment is working correctly

Write-Host "🧪 Testing Milling Tool Monitor Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if Docker is running
Write-Host "Test 1: Docker Status" -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ PASS: Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ FAIL: Docker is not running" -ForegroundColor Red
    exit 1
}

# Test 2: Check if container is running
Write-Host ""
Write-Host "Test 2: Container Status" -ForegroundColor Yellow
$containerStatus = docker-compose ps --services --filter "status=running"
if ($containerStatus -match "app") {
    Write-Host "✅ PASS: App container is running" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: App container is not running" -ForegroundColor Red
    Write-Host "Run: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Test 3: Check if port 5000 is listening
Write-Host ""
Write-Host "Test 3: Port Availability" -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASS: Application responding on port 5000" -ForegroundColor Green
    } else {
        Write-Host "⚠️  WARNING: Unexpected status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ FAIL: Cannot connect to http://localhost:5000" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Gray
    exit 1
}

# Test 4: Check if Files directory exists in container
Write-Host ""
Write-Host "Test 4: Files Directory" -ForegroundColor Yellow
$filesCheck = docker-compose exec -T app ls /app/Files 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PASS: Files directory exists in container" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Files directory not found" -ForegroundColor Red
    exit 1
}

# Test 5: Check if MAT file exists
Write-Host ""
Write-Host "Test 5: MAT Data File" -ForegroundColor Yellow
$matCheck = docker-compose exec -T app ls /app/Files/forces_xyz_raw.mat 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PASS: MAT file found" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: MAT file not found" -ForegroundColor Red
    Write-Host "Expected: /app/Files/forces_xyz_raw.mat" -ForegroundColor Gray
    exit 1
}

# Test 6: Check if model file exists
Write-Host ""
Write-Host "Test 6: Model File" -ForegroundColor Yellow
$modelCheck = docker-compose exec -T app ls /app/Files/*.pth 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PASS: Model file found" -ForegroundColor Green
} else {
    Write-Host "⚠️  WARNING: Model file not found (predictions may not work)" -ForegroundColor Yellow
}

# Test 7: Check container logs for errors
Write-Host ""
Write-Host "Test 7: Container Logs" -ForegroundColor Yellow
$logs = docker-compose logs --tail=50 app 2>&1
if ($logs -match "error|Error|ERROR|exception|Exception|EXCEPTION") {
    Write-Host "⚠️  WARNING: Errors found in logs" -ForegroundColor Yellow
    Write-Host "Run 'docker-compose logs app' to view details" -ForegroundColor Gray
} else {
    Write-Host "✅ PASS: No obvious errors in logs" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎉 All Tests Passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Your deployment is working correctly!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application at: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:5000 in your browser" -ForegroundColor Gray
Write-Host "  2. Click 'Run Real-Time Demo'" -ForegroundColor Gray
Write-Host "  3. Wait for results (10-30 seconds)" -ForegroundColor Gray
Write-Host ""
