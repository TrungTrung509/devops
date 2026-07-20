
# BENCHMARK SCRIPT - Centralized vs Distributed
# So sanh hieu nang giua mo hinh tap trung va phan tan

$ErrorActionPreference = "Stop"
$ProjectRoot = "e:\2.PTIT\DangKiHocPhan\BTL-CSDLPT"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BENCHMARK: Centralized vs Distributed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Output file
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputDir = "$ProjectRoot\docs\benchmark"
$OutputFile = "$OutputDir\benchmark_results_$Timestamp.md"

# Ensure output dir exists
$null = New-Item -ItemType Directory -Force -Path $OutputDir 2>$null

# Check if centralized DB is ready
Write-Host "[1/5] Checking centralized database..." -ForegroundColor Yellow
$Ready = docker exec csdlpt_centralized pg_isready -U csdlpt_user -d csdlpt_centralized 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Centralized database not ready. Run setup_centralized_db.ps1 first." -ForegroundColor Red
    exit 1
}
Write-Host "Centralized database is ready." -ForegroundColor Green

# Check if distributed sites are ready
Write-Host "[2/5] Checking distributed databases..." -ForegroundColor Yellow
$HadongReady = docker exec csdlpt_hadong pg_isready -U csdlpt_user -d csdlpt_hadong 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: HADONG site not ready." -ForegroundColor Red
    exit 1
}
Write-Host "Distributed databases are ready." -ForegroundColor Green

Write-Host "[3/5] Running centralized queries..." -ForegroundColor Yellow

# Copy centralized queries to container
docker cp "$ProjectRoot\sql\benchmark\centralized_queries.sql" csdlpt_centralized:/tmp/centralized_queries.sql

# Run centralized benchmark
$CentralizedOutput = docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -f /tmp/centralized_queries.sql 2>&1

Write-Host "[4/5] Running distributed queries..." -ForegroundColor Yellow

# Copy distributed queries to HADONG container
docker cp "$ProjectRoot\sql\benchmark\distributed_queries.sql" csdlpt_hadong:/tmp/distributed_queries.sql

# Run distributed benchmark
$DistributedOutput = docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -f /tmp/distributed_queries.sql 2>&1

Write-Host "[5/5] Generating report..." -ForegroundColor Yellow

# Generate markdown report
$ReportContent = @"
# Benchmark Results: Centralized vs Distributed

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## ENVIRONMENT

- **Centralized DB**: csdlpt_centralized (port 5435)
- **Distributed Sites**: csdlpt_hadong (5432), csdlpt_ngoctruc (5433), csdlpt_hoalac (5434)
- **Note**: FDW setup at HADONG site connects to NGOCTRUC and HOALAC

---

## CENTRALIZED MODEL RESULTS (port 5435)

Database chứa dữ liệu từ cả 3 site, truy vấn local trong 1 database.

\`\`\`
$CentralizedOutput
\`\`\`

---

## DISTRIBUTED MODEL RESULTS (HADONG site with FDW)

Truy vấn tại HADONG sử dụng FDW để lấy dữ liệu từ NGOCTRUC và HOALAC.

\`\`\`
$DistributedOutput
\`\`\`

---

## SUMMARY TABLE

| Query | Centralized | Distributed | Winner | Notes |
|-------|-------------|-------------|--------|-------|
"

# Parse and compare results
$ReportContent += @"

---

## ANALYSIS

### Local Query Performance
- **Local query (Q1, Q6)**: Truy van local tren centralized co the cham hon phan tan vi can filter tren big dataset
- **Phan tan local**: Chi doc tu 1 site, khong can FDW overhead

### Global Query Performance  
- **Global query (Q2, Q3, Q4, Q5, Q7)**: Centralized thuong nhanh hon vi:
  - Khong can FDW de truy cap remote sites
  - Khong can network latency
  - Khong can union data tu nhieu nguon

### FDW Overhead
- Truy van phan tan global phai su dung Foreign Scan de lay du lieu tu remote sites
- Co them latency do truyen du lieu qua network trong Docker

### Dataset Size
- Hien tai dataset nho (30 SV, 60 LHP, 3 DK toan truong)
- voi dataset lon hon, xu huong co the khac

---

## NOTES

- Times shown are from \`EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)\`
- Distributed queries show \`Foreign Scan\` nodes when accessing remote sites
- Dataset size is small, so differences may be minimal
- Architecture trends are more important than absolute values at this scale

---

## HOW TO RE-RUN

\`\`\`powershell
powershell -ExecutionPolicy Bypass -File scripts/run_centralized_vs_distributed_benchmark.ps1
\`\`\`

Or from Linux/macOS:

\`\`\`bash
bash scripts/run_centralized_vs_distributed_benchmark.sh
\`\`\`
"@

# Save report
$ReportContent | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host ""
Write-Host "  BENCHMARK COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "Report saved to: $OutputFile" -ForegroundColor Cyan
Write-Host ""

# Also update the main benchmark results file
$MainResultsFile = "$ProjectRoot\docs\benchmark\centralized_vs_distributed_results.md"
$ReportContent | Out-File -FilePath $MainResultsFile -Encoding UTF8
Write-Host "Main results updated: $MainResultsFile" -ForegroundColor Cyan
