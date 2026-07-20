-- [Bước 1-HL]: Mở transaction ghim (pinned connection) trên site Hòa Lạc
BEGIN;

-- [Bước 1a-HL]: Truy vấn thăm dò lớp học phần mới trên site Hòa Lạc để xác định site sở hữu 
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01'
LIMIT 1;

-- PHA ĐẦU: KIỂM TRA NHANH KHÔNG KHÓA (SNAPSHOT CHECK)
-- [Bước 2-HL]: Kiểm tra sự tồn tại, trạng thái mở lớp, và sĩ số hiện tại của lớp mới 'HOALAC_CSDLPT_01'
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01';
-- (Kiểm tra logic: nếu không tồn tại, TrangThaiLop != 'Mo' hoặc SiSoHienTai >= SiSoToiDa -> Rollback)

-- [Bước 3-HL]: Lấy thông tin lịch học của lớp mới 'HOALAC_CSDLPT_01' tại Hòa Lạc
SELECT "ThuTrongTuan", "TietBatDau", "SoTiet" 
FROM "LichHoc" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01';

-- [Bước 4-HL]: Lấy lịch học các môn chéo khác của SV tại site Hòa Lạc để đối chiếu trùng lịch
SELECT lh."MaLopHP", lh."ThuTrongTuan", lh."TietBatDau", lh."SoTiet"
FROM "DangKy" dk
JOIN "LichHoc" lh ON dk."MaLopHP" = lh."MaLopHP"
WHERE dk."userId" = 'SVHD26CNTT001' 
  AND dk."MaHocKy" = 'HK251'
  AND dk."TrangThaiDangKy" = 'DaDangKy';

-- PHA 1: PREPARE PHASE
-- [Bước 5-HL]: Xin khóa Advisory Lock cho SV trong học kỳ
SELECT pg_try_advisory_lock(456987123654) AS user_semester_lock_granted;

-- [Bước 6-HL]: Xin khóa Advisory Lock cho lớp học phần mới
SELECT pg_try_advisory_lock(789123456789) AS target_section_lock_granted;
-- (Nếu bất kỳ khóa nào trả về false -> Giải phóng các khóa đã chiếm, Rollback và thoát sớm)

-- [Bước 7-HL]: Ghi nhận thông tin giao dịch phân tán ở trạng thái INIT
INSERT INTO "DangKy_3PC" (
    "TxnId", "CoordinatorSite", "SiteId", "UserId", "Action", 
    "State", "TargetMaLopHP", "TargetMaHP", "TargetMaHocKy", "OldMaLopHP", "Payload"
) VALUES (
    'txn_3pc_switch_demo_987654', 'HADONG', 'HOALAC', 'SVHD26CNTT001', 'SWITCH', 
    'INIT', 'HOALAC_CSDLPT_01', 'CSDLPT', 'HK251', 'HADONG_CSDLPT_01', 
    '{"ma_sv": "SVHD26CNTT001", "ma_lop_hp_moi": "HOALAC_CSDLPT_01", "ma_lop_hp_cu": "HADONG_CSDLPT_01"}'
);

-- [Bước 8-HL]: SELECT FOR UPDATE để khóa dòng (Row Lock)
SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01' 
FOR UPDATE;
-- (nếu TrangThaiLop != 'Mo' hoặc SiSoHienTai >= SiSoToiDa -> Rollback)

-- [Bước 9-HL]: Cập nhật trạng thái giao dịch sang PREPARED
UPDATE "DangKy_3PC" 
SET "State" = 'PREPARED', "Message" = 'Tất cả participant đã hoàn tất prepare', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- PHA 2: PRE-COMMIT PHASE
-- [Bước 10-HL]: Cập nhật trạng thái giao dịch sang PRECOMMIT (Điểm không thể quay đầu)
UPDATE "DangKy_3PC" 
SET "State" = 'PRECOMMIT', "Message" = 'Coordinator đã chuyển sang pha pre-commit', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- PHA 3: COMMIT PHASE
-- [Bước 11-HL]: Chèn bản ghi đăng ký của SV vào bảng DangKy của Hòa Lạc
INSERT INTO "DangKy" ("userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy")
VALUES ('SVHD26CNTT001', 'SVHD26CNTT001', 'HOALAC_CSDLPT_01', 'CSDLPT', 'HK251', NOW(), 'DaDangKy', 1);

-- [Bước 12-HL]: Cập nhật tăng sĩ số hiện tại của lớp học phần mới lên 1
UPDATE "LopHocPhan"
SET "SiSoHienTai" = "SiSoHienTai" + 1
WHERE "MaLopHP" = 'HOALAC_CSDLPT_01';

-- [Bước 13-HL]: Cập nhật trạng thái giao dịch sang COMMITTED
UPDATE "DangKy_3PC" 
SET "State" = 'COMMITTED', "Message" = 'Tất cả participant đã commit thành công', "UpdatedAt" = NOW()
WHERE "TxnId" = 'txn_3pc_switch_demo_987654';

-- [Bước 14-HL]: Hoàn tất transaction cục bộ trên site Hòa Lạc
COMMIT;

-- [Bước 15-HL]: Giải phóng Advisory Lock cho sinh viên
SELECT pg_advisory_unlock(456987123654);

-- [Bước 16-HL]: Giải phóng Advisory Lock cho lớp học phần mới
SELECT pg_advisory_unlock(789123456789);
