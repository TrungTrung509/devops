
# SETUP CENTRALIZED DATABASE
# Chạy script này sau khi container postgres_centralized đã chạy

$ErrorActionPreference = "Stop"
$ProjectRoot = "e:\2.PTIT\DangKiHocPhan\BTL-CSDLPT"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP CENTRALIZED DATABASE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start container
Write-Host "[1/5] Starting postgres_centralized container..." -ForegroundColor Yellow
docker compose -f "$ProjectRoot\docker\docker-compose.yml" up -d postgres_centralized

# Wait for container to be ready
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
$MaxWait = 60
$Waited = 0
while ($Waited -lt $MaxWait) {
    $Ready = docker exec csdlpt_centralized pg_isready -U csdlpt_user -d csdlpt_centralized 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database is ready!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $Waited += 2
}
if ($Waited -ge $MaxWait) {
    Write-Host "ERROR: Database did not become ready in $MaxWait seconds" -ForegroundColor Red
    exit 1
}

# Step 2: Drop and recreate schema, then enable dblink
Write-Host "[2/5] Dropping old schema and enabling dblink..." -ForegroundColor Yellow
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; CREATE EXTENSION IF NOT EXISTS dblink;"

# Step 3: Create schema
Write-Host "[3/5] Creating centralized schema..." -ForegroundColor Yellow
docker cp "$ProjectRoot\db\centralized\01_centralized_schema.sql" csdlpt_centralized:/tmp/centralized_schema.sql
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -f /tmp/centralized_schema.sql

# Step 4: Import data from 3 sites
Write-Host "[4/5] Importing data from 3 sites..." -ForegroundColor Yellow
docker cp "$ProjectRoot\db\centralized\02_import_data.sql" csdlpt_centralized:/tmp/import_data.sql
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -f /tmp/import_data.sql

# Step 5: Show summary
Write-Host "[5/5] Verifying data..." -ForegroundColor Yellow
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -c "SELECT 'SinhVien' AS tbl, COUNT(*) FROM \"SinhVien\" UNION ALL SELECT 'GiangVien', COUNT(*) FROM \"GiangVien\" UNION ALL SELECT 'PhongHoc', COUNT(*) FROM \"PhongHoc\" UNION ALL SELECT 'LopHocPhan', COUNT(*) FROM \"LopHocPhan\" UNION ALL SELECT 'LichHoc', COUNT(*) FROM \"LichHoc\" UNION ALL SELECT 'DangKy', COUNT(*) FROM \"DangKy\";"

Write-Host ""
Write-Host "  CENTRALIZED DATABASE SETUP COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "Database: csdlpt_centralized (port 5435)" -ForegroundColor Cyan
Write-Host "User: csdlpt_user" -ForegroundColor Cyan
Write-Host "Password: csdlpt_pass" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connect from host:" -ForegroundColor Yellow
Write-Host "  psql -h localhost -p 5435 -U csdlpt_user -d csdlpt_centralized" -ForegroundColor White
Write-Host ""
Write-Host "Run benchmark:" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/run_centralized_vs_distributed_benchmark.ps1" -ForegroundColor White
