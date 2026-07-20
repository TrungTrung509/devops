-- [Bước 1-HD]: Mở transaction ghim (pinned connection) trên site Hà Đông
BEGIN;

-- [Bước 1a-HD]: Truy vấn thăm dò lớp học phần mới trên site Hà Đông để xác định site sở hữu
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01'
LIMIT 1;

-- PHA ĐẦU: SNAPSHOT CHECK
-- [Bước 2-HD]: Kiểm tra xem sinh viên đã đăng ký học phần này ở các lớp khác trong cùng học kỳ chưa
SELECT COUNT(*) AS duplicate_course_count
FROM "DangKy" 
WHERE "userId" = 'SVHD26CNTT001' 
  AND "MaHP" = 'CSDLPT' 
  AND "MaHocKy" = 'HK251' 
  AND "TrangThaiDangKy" = 'DaDangKy'
  AND "MaLopHP" != 'HADONG_CSDLPT_01'; -- Loại trừ lớp cũ đang muốn đổi

-- [Bước 3-HD]: Lấy danh sách lịch học hiện tại của sinh viên trong học kỳ HK251
SELECT lh."MaLopHP", lh."ThuTrongTuan", lh."TietBatDau", lh."SoTiet"
FROM "DangKy" dk
JOIN "LichHoc" lh ON dk."MaLopHP" = lh."MaLopHP"
WHERE dk."userId" = 'SVHD26CNTT001' 
  AND dk."MaHocKy" = 'HK251'
  AND dk."TrangThaiDangKy" = 'DaDangKy'
  AND dk."MaLopHP" != 'HADONG_CSDLPT_01'; -- Loại trừ lịch lớp cũ đang muốn đổi

-- PHA 1: PREPARE
-- [Bước 4-HD]: Xin khóa Advisory Lock cho SV trong học kỳ
SELECT pg_try_advisory_lock(456987123654) AS user_semester_lock_granted;

-- [Bước 5-HD]: Xin khóa Advisory Lock cho lớp học phần cũ
SELECT pg_try_advisory_lock(123456789123) AS old_section_lock_granted;
-- (Nếu bất kỳ khóa nào trả về false)

-- [Bước 6-HD]: Khởi tạo log giao dịch phân tán ở trạng thái INIT
INSERT INTO "DangKy_3PC" (
    "TxnId", "CoordinatorSite", "SiteId", "UserId", "Action", 
    "State", "TargetMaLopHP", "TargetMaHP", "TargetMaHocKy", "OldMaLopHP", "Payload"
) VALUES (
    'txn_3pc_switch_demo_987654', 'HADONG', 'HADONG', 'SVHD26CNTT001', 'SWITCH', 
    'INIT', 'HOALAC_CSDLPT_01', 'CSDLPT', 'HK251', 'HADONG_CSDLPT_01', 
    '{"ma_sv": "SVHD26CNTT001", "ma_lop_hp_moi": "HOALAC_CSDLPT_01", "ma_lop_hp_cu": "HADONG_CSDLPT_01"}'
);

-- [Bước 7-HD]: SELECT FOR UPDATE để khóa dòng
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HADONG_CSDLPT_01' 
FOR UPDATE;

-- [Bước 8-HD]: Cập nhật trạng thái giao dịch sang PREPARED
UPDATE "DangKy_3PC" 
SET "State" = 'PREPARED', "Message" = 'Tất cả participant đã hoàn tất prepare', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- PHA 2: PRE-COMMIT 
-- [Bước 9-HD]: Cập nhật trạng thái giao dịch sang PRECOMMIT
UPDATE "DangKy_3PC" 
SET "State" = 'PRECOMMIT', "Message" = 'Coordinator đã chuyển sang pha pre-commit', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- PHA 3: COMMIT
-- [Bước 10-HD]: Xóa bản ghi đăng ký cũ
DELETE FROM "DangKy" 
WHERE "userId" = 'SVHD26CNTT001' AND "MaLopHP" = 'HADONG_CSDLPT_01';

-- [Bước 11-HD]: Cập nhật giảm sĩ số hiện tại của lớp cũ đi 1
UPDATE "LopHocPhan"
SET "SiSoHienTai" = GREATEST("SiSoHienTai" - 1, 0)
WHERE "MaLopHP" = 'HADONG_CSDLPT_01';

-- [Bước 12-HD]: Đồng bộ liên kết đăng ký chéo cơ sở sang lớp mới ở Hòa Lạc
INSERT INTO "DangKy_ChuyenCoSo" ("userId", "MaLopHP", "MaHP", "TargetSite", "Timestamp")
VALUES ('SVHD26CNTT001', 'HOALAC_CSDLPT_01', 'CSDLPT', 'HOALAC', NOW())
ON CONFLICT ("userId", "MaLopHP") 
DO UPDATE SET "Timestamp" = NOW();

-- [Bước 13-HD]: Cập nhật trạng thái giao dịch sang COMMITTED
UPDATE "DangKy_3PC" 
SET "State" = 'COMMITTED', "Message" = 'Tất cả participant đã commit thành công', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- [Bước 14-HD]: Hoàn tất transaction cục bộ trên site Hà Đông
COMMIT;

-- [Bước 15-HD]: Giải phóng Advisory Lock cho sinh viên
SELECT pg_advisory_unlock(456987123654);

-- [Bước 16-HD]: Giải phóng Advisory Lock cho lớp học phần cũ
SELECT pg_advisory_unlock(123456789123);
