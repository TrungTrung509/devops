@echo off
chcp 65001 >nul
echo  FULL RESET - Recreate All with UTF8 + Clean Data
echo.
echo [WARNING] This will DELETE all existing data!
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" exit /b
echo.

echo [1/6] Stopping containers and removing volumes...
docker compose down -v
echo Done.

echo.
echo [2/6] Starting containers fresh (will init with UTF8)...
docker compose up -d
echo Done.

echo.
echo [3/6] Waiting for PostgreSQL to be ready (30s)...
timeout /t 30 /nobreak >nul

echo.
echo [4/6] Verifying encoding...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT datname, encoding, pg_encoding_to_char(encoding) FROM pg_database;"
echo.

echo [5/6] Checking data quality...
echo --- HADONG ---
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaHP, TenHP FROM hocphan LIMIT 3;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaKhoa, TenKhoa FROM khoa;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaSV, Ho, Ten FROM sinhvien LIMIT 3;"
echo.
echo --- NGOCTRUC ---
docker exec csdlpt_ngoctruc psql -U csdlpt_user -d csdlpt_ngoctruc -c "SELECT MaSV, Ho, Ten FROM sinhvien LIMIT 3;"
echo.
echo --- HOALAC ---
docker exec csdlpt_hoalac psql -U csdlpt_user -d csdlpt_hoalac -c "SELECT MaSV, Ho, Ten FROM sinhvien LIMIT 3;"

echo.
echo [6/6] Summary...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT 'SinhVien' as tbl, COUNT(*) FROM sinhvien UNION ALL SELECT 'GiangVien', COUNT(*) FROM giangvien UNION ALL SELECT 'PhongHoc', COUNT(*) FROM phonghoc UNION ALL SELECT 'LopHocPhan', COUNT(*) FROM lophocphan UNION ALL SELECT 'LichHoc', COUNT(*) FROM lichhoc;"

echo.
echo  Done! Check Vietnamese data above.
pause
