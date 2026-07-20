$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== BAT DAU K6 BENCHMARK (CoSo + Khoa song song) ===" -ForegroundColor Cyan
Write-Host "Grafana: http://localhost:3001  |  Prometheus: http://localhost:9091" -ForegroundColor DarkGray

$p1 = Start-Process -FilePath "docker" `
    -ArgumentList "run --rm -i --network benchmark_bench_network grafana/k6 run -" `
    -RedirectStandardInput "$Root\CoSo\k6_test.js" `
    -PassThru -NoNewWindow

$p2 = Start-Process -FilePath "docker" `
    -ArgumentList "run --rm -i --network benchmark_bench_network grafana/k6 run -" `
    -RedirectStandardInput "$Root\Khoa\k6_test.js" `
    -PassThru -NoNewWindow

Write-Host "CoSo PID: $($p1.Id)  |  Khoa PID: $($p2.Id)" -ForegroundColor Green
Write-Host "Dang chay (~2 phut 30 giay)..." -ForegroundColor Cyan

$p1, $p2 | Wait-Process

Write-Host ""
Write-Host "=== BENCHMARK HOAN THANH ===" -ForegroundColor Cyan
