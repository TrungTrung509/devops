@echo off
chcp 65001 >nul
echo  FIX ENCODING - Recreate Database with UTF8
echo.
echo [WARNING] This will DELETE all existing data!
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" exit /b
echo.

echo [1/5] Stopping containers and removing volumes...
docker compose down -v
echo Done.

echo.
echo [2/5] Starting containers (will init with UTF8)...
docker compose up -d
echo Done.

echo.
echo [3/5] Waiting for PostgreSQL to be ready...
timeout /t 15 /nobreak >nul

echo.
echo [4/5] Verifying encoding...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT datname, encoding FROM pg_database WHERE datname = 'csdlpt_hadong';"
echo.

echo [5/5] Checking data...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaHP, TenHP FROM hocphan LIMIT 3;"
echo.
echo  Done! Check encoding and data above.
pause
