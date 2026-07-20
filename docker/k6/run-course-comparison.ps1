param(
    [Parameter(Mandatory = $true)]
    [string]$Username,

    [Parameter(Mandatory = $true)]
    [string]$Password,

    [string]$TargetSite = "HADONG",
    [int]$Vus = 10,
    [int]$Iterations = 100,
    [int]$RemoteIterations = 100
)

$composeArgs = @(
    "--profile", "benchmark",
    "run", "--rm",
    "-e", "BENCH_USERNAME=$Username",
    "-e", "BENCH_PASSWORD=$Password",
    "-e", "BENCH_TARGET_SITE=$TargetSite",
    "-e", "BENCH_VUS=$Vus",
    "-e", "BENCH_ITERATIONS=$Iterations",
    "-e", "BENCH_REMOTE_ITERATIONS=$RemoteIterations"
)

Write-Host "Running local benchmark..." -ForegroundColor Cyan
docker compose @composeArgs k6 run /scripts/course-local.js
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Waiting 20s for Prometheus scrape..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "Running remote benchmark..." -ForegroundColor Cyan
docker compose @composeArgs k6 run /scripts/course-remote.js
exit $LASTEXITCODE
