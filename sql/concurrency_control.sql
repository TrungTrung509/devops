-- CƠ SỞ DỮ LIỆU PHÂN TÁN - HỆ THỐNG ĐĂNG KÝ HỌC PHẦN
-- KỊCH BẢN XỬ LÝ ĐỒNG THỜI & ĐẢM BẢO SĨ SỐ (YÊU CẦU 5)

-- 1. TRIGGER KIỂM TRA SĨ SỐ VÀ TỰ ĐỘNG CẬP NHẬT SĨ SỐ
-- Chạy script này trên cả 3 database site: HADONG, NGOCTRUC, HOALAC

-- Hàm xử lý logic trigger
CREATE OR REPLACE FUNCTION check_and_update_siso()
RETURNS TRIGGER AS $$
DECLARE
    v_siso_hientai INT;
    v_siso_toida INT;
    v_trangthai VARCHAR(20);
BEGIN
    -- Trường hợp 1: Khi có sinh viên đăng ký mới (INSERT)
    IF (TG_OP = 'INSERT') THEN
        -- Khóa dòng lớp học phần trên site để đọc sĩ số chính xác nhất, tránh tranh chấp
        SELECT "SiSoHienTai", "SiSoToiDa", "TrangThaiLop"
        INTO v_siso_hientai, v_siso_toida, v_trangthai
        FROM "LopHocPhan"
        WHERE "MaLopHP" = NEW."MaLopHP"
        FOR UPDATE; -- Khóa dòng (Pessimistic Locking)

        -- Kiểm tra trạng thái lớp học
        IF v_trangthai != 'Mo' THEN
            RAISE EXCEPTION 'Lớp học phần % đang ở trạng thái đóng hoặc đã hủy!', NEW."MaLopHP";
        END IF;

        -- Kiểm tra giới hạn sĩ số tối đa
        IF v_siso_hientai >= v_siso_toida THEN
            RAISE EXCEPTION 'Lớp học phần % đã đạt sĩ số tối đa (%/%)! Không thể đăng ký thêm.', 
                            NEW."MaLopHP", v_siso_hientai, v_siso_toida;
        END IF;

        -- Nếu hợp lệ, tự động cộng thêm 1 vào sĩ số hiện tại của lớp
        UPDATE "LopHocPhan"
        SET "SiSoHienTai" = "SiSoHienTai" + 1
        WHERE "MaLopHP" = NEW."MaLopHP";

        RETURN NEW;

    -- Trường hợp 2: Khi sinh viên hủy đăng ký (DELETE)
    ELSIF (TG_OP = 'DELETE') THEN
        -- Tự động trừ đi 1 sĩ số hiện tại của lớp (đảm bảo không âm dưới 0)
        UPDATE "LopHocPhan"
        SET "SiSoHienTai" = GREATEST("SiSoHienTai" - 1, 0)
        WHERE "MaLopHP" = OLD."MaLopHP";

        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Tạo Trigger gắn vào bảng DangKy (Chạy trước khi INSERT hoặc DELETE)
CREATE OR REPLACE TRIGGER trg_check_and_update_siso
BEFORE INSERT OR DELETE ON "DangKy"
FOR EACH ROW
EXECUTE FUNCTION check_and_update_siso();


-- 2. GIAO DỊCH SỬ DỤNG KHÓA DÒNG (PESSIMISTIC LOCKING)
-- Minh họa giao dịch đăng ký học phần an toàn mức CSDL

-- Bắt đầu giao dịch
BEGIN;

-- Bước A: Đọc và khóa dòng thông tin lớp học phần
-- Các giao dịch khác muốn sửa đổi lớp này sẽ phải đợi cho đến khi transaction này COMMIT/ROLLBACK
SELECT "SiSoHienTai", "SiSoToiDa" 
FROM "LopHocPhan" 
WHERE "MaLopHP" = 'HADONG_CSDLPT_01' 
FOR UPDATE;

-- Bước B: Kiểm tra trùng lịch học của sinh viên
-- (Nếu kết quả trả về > 0 tức là bị trùng lịch -> gọi ROLLBACK)
SELECT COUNT(*) 
FROM "LichHoc" lh
JOIN "DangKy" dk ON dk."MaLopHP" = lh."MaLopHP"
WHERE dk."userId" = 'SVHD26CNTT001' 
  AND lh."ThuTrongTuan" = 2 -- Ví dụ lớp học mở vào thứ 2
  AND lh."TietBatDau" = 1;  -- Ví dụ lớp học bắt đầu từ tiết 1

-- Bước C: Thực hiện chèn thông tin đăng ký học phần
-- (Lúc này Trigger check_and_update_siso sẽ tự động kích hoạt để kiểm tra sĩ số và tăng sĩ số lớp lên)
INSERT INTO "DangKy" ("userId", "MaLopHP", "TrangThaiDangKy") 
VALUES ('SVHD26CNTT001', 'HADONG_CSDLPT_01', 'ThanhCong');

-- Bước D: Hoàn tất giao dịch thành công và giải phóng khóa dòng
COMMIT;

-- HOẶC khi có lỗi (Trùng lịch / Lớp đã đầy):
-- ROLLBACK;


-- 3. GIAO DỊCH PHÂN TÁN TWO-PHASE COMMIT (2PC)
-- Minh họa đăng ký chéo cơ sở: Sinh viên Hà Đông đăng ký lớp ở Hòa Lạc

-- PHA 1: THỰC THI VÀ CHUẨN BỊ (PREPARE) TRÊN CẢ 2 SITE

-- Chạy trên Site Hà Đông (csdlpt_hadong - Cổng 5432)
BEGIN;
INSERT INTO "NhatKyThaoTac" ("userId", "HanhDong", "NgayTao") 
VALUES ('SVHD26CNTT001', 'Đăng ký chéo cơ sở lớp HOALAC_CSDLPT_01', CURRENT_TIMESTAMP);
PREPARE TRANSACTION 'txn_dangky_cheo_hadong_001';

-- Chạy trên Site Hòa Lạc (csdlpt_hoalac - Cổng 5434)
BEGIN;
INSERT INTO "DangKy" ("userId", "MaLopHP", "TrangThaiDangKy") 
VALUES ('SVHD26CNTT001', 'HOALAC_CSDLPT_01', 'ThanhCong');
PREPARE TRANSACTION 'txn_dangky_cheo_hoalac_001';


-- PHA 2: XÁC NHẬN CAM KẾT (COMMIT) HOẶC HỦY BỎ (ROLLBACK)

-- Trường hợp A: Cả 2 site đều chuẩn bị thành công (Không lỗi ràng buộc)
-- Chạy trên Site Hà Đông:
COMMIT PREPARED 'txn_dangky_cheo_hadong_001';
-- Chạy trên Site Hòa Lạc:
COMMIT PREPARED 'txn_dangky_cheo_hoalac_001';

-- Trường hợp B: Một trong hai site bị lỗi hoặc mất mạng giữa chừng
-- Chạy trên Site Hà Đông:
ROLLBACK PREPARED 'txn_dangky_cheo_hadong_001';
-- Chạy trên Site Hòa Lạc:
ROLLBACK PREPARED 'txn_dangky_cheo_hoalac_001';


-- 4. DEMO TÍNH TRONG SUỐT PHÂN MẢNH (FRAGMENTATION TRANSPARENCY)
-- Demo tại site Hà Đông (csdlpt_hadong - Cổng 5432)

-- Bước A: Tạo View toàn cục Global_SinhVien
-- Phép UNION ALL gộp dữ liệu từ site local và các site foreign qua FDW
CREATE OR REPLACE VIEW Global_SinhVien AS
SELECT * FROM "SinhVien"
UNION ALL
SELECT * FROM fdw_ngoctruc."SinhVien"
UNION ALL
SELECT * FROM fdw_hoalac."SinhVien";

-- Bước B: Viết Hàm trigger INSTEAD OF xử lý việc ghi dữ liệu vào View
-- Khi người dùng chèn vào View Global_SinhVien, hàm này sẽ tự động định tuyến
CREATE OR REPLACE FUNCTION tg_insert_global_sinhvien()
RETURNS TRIGGER AS $$
BEGIN
    -- Nếu MaCoSo là HADONG, chèn thẳng vào bảng local Hà Đông
    IF NEW."MaCoSo" = 'HADONG' THEN
        INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "TrangThai", "MaCoSo", "MaKhoa", "NgayNhapHoc")
        VALUES (NEW."MaSV", NEW."userId", NEW."Ho", NEW."Ten", NEW."NgaySinh", NEW."GioiTinh", NEW."SDT", NEW."DiaChi", NEW."TrangThai", NEW."MaCoSo", NEW."MaKhoa", NEW."NgayNhapHoc");

    -- Nếu MaCoSo là NGOCTRUC, chèn vào bảng ngoại lai Ngọc Trục qua FDW
    ELSIF NEW."MaCoSo" = 'NGOCTRUC' THEN
        INSERT INTO fdw_ngoctruc."SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "TrangThai", "MaCoSo", "MaKhoa", "NgayNhapHoc")
        VALUES (NEW."MaSV", NEW."userId", NEW."Ho", NEW."Ten", NEW."NgaySinh", NEW."GioiTinh", NEW."SDT", NEW."DiaChi", NEW."TrangThai", NEW."MaCoSo", NEW."MaKhoa", NEW."NgayNhapHoc");

    -- Nếu MaCoSo là HOALAC, chèn vào bảng ngoại lai Hòa Lạc qua FDW
    ELSIF NEW."MaCoSo" = 'HOALAC' THEN
        INSERT INTO fdw_hoalac."SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "TrangThai", "MaCoSo", "MaKhoa", "NgayNhapHoc")
        VALUES (NEW."MaSV", NEW."userId", NEW."Ho", NEW."Ten", NEW."NgaySinh", NEW."GioiTinh", NEW."SDT", NEW."DiaChi", NEW."TrangThai", NEW."MaCoSo", NEW."MaKhoa", NEW."NgayNhapHoc");

    ELSE
        RAISE EXCEPTION 'Mã cơ sở % không hợp lệ trên hệ thống!', NEW."MaCoSo";
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Bước C: Tạo Trigger INSTEAD OF INSERT trên View Global_SinhVien
CREATE OR REPLACE TRIGGER trg_insert_global_sinhvien
INSTEAD OF INSERT ON Global_SinhVien
FOR EACH ROW
EXECUTE FUNCTION tg_insert_global_sinhvien();

