-- [Bước 1-NT]: Mở transaction ghim (pinned connection) trên site Ngọc Trục
BEGIN;

-- [Bước 1a-NT]: Truy vấn thăm dò lớp học phần mới trên site Ngọc Trục để xác định site sở hữu
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01'
LIMIT 1;
-- PHA ĐẦU: KIỂM TRA NHANH KHÔNG KHÓA (SNAPSHOT CHECK)
-- [Bước 3-NT]: Lấy danh sách lịch học hiện tại của sinh viên ở site Ngọc Trục trong học kỳ HK251
SELECT lh."MaLopHP", lh."ThuTrongTuan", lh."TietBatDau", lh."SoTiet"
FROM "DangKy" dk
JOIN "LichHoc" lh ON dk."MaLopHP" = lh."MaLopHP"
WHERE dk."userId" = 'SVHD26CNTT001' 
  AND dk."MaHocKy" = 'HK251'
  AND dk."TrangThaiDangKy" = 'DaDangKy';
ROLLBACK;
