@echo off
chcp 65001 >nul
echo  FIX CORRUPTED DATA - Reinsert with correct UTF-8
echo.

echo [1/6] Cleaning corrupted data from HADONG...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "TRUNCATE TABLE dangky, lichhoc, lophocphan, sinhvien, giangvien, phonghoc CASCADE;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "TRUNCATE TABLE dangky_log, auditlog;"
echo Done.

echo.
echo [2/6] Cleaning corrupted data from NGOCTRUC...
docker exec csdlpt_ngoctruc psql -U csdlpt_user -d csdlpt_ngoctruc -c "TRUNCATE TABLE dangky, lichhoc, lophocphan, sinhvien, giangvien, phonghoc CASCADE;"
docker exec csdlpt_ngoctruc psql -U csdlpt_user -d csdlpt_ngoctruc -c "TRUNCATE TABLE dangky_log, auditlog;"
echo Done.

echo.
echo [3/6] Cleaning corrupted data from HOALAC...
docker exec csdlpt_hoalac psql -U csdlpt_user -d csdlpt_hoalac -c "TRUNCATE TABLE dangky, lichhoc, lophocphan, sinhvien, giangvien, phonghoc CASCADE;"
docker exec csdlpt_hoalac psql -U csdlpt_user -d csdlpt_hoalac -c "TRUNCATE TABLE dangky_log, auditlog;"
echo Done.

echo.
echo [4/6] Reinserting HADONG data...
docker exec -i csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong << 'ENDSQL'
-- GiangVien HADONG
INSERT INTO GiangVien (MaGV, Ho, Ten, HocVi, HocHam, Email, SoDienThoai, MaCoSo, MaKhoa, TrangThai, NgayVaoLam) VALUES
('HADONGGV001', 'Nguyễn', 'An', 'TS', 'GTV', 'an.nguyen@gv.ptit.edu.vn', '0987654321', 'HADONG', 'CNTT', 'DangCongTac', '2015-09-01'),
('HADONGGV002', 'Trần', 'Bình', 'ThS', NULL, 'binh.tran@gv.ptit.edu.vn', '0987654322', 'HADONG', 'CNTT', 'DangCongTac', '2016-09-01'),
('HADONGGV003', 'Lê', 'Cường', 'CN', NULL, 'cuong.le@gv.ptit.edu.vn', '0987654323', 'HADONG', 'CNTT', 'DangCongTac', '2017-09-01'),
('HADONGGV004', 'Phạm', 'Dung', 'TS', NULL, 'dung.pham@gv.ptit.edu.vn', '0987654324', 'HADONG', 'ATTT', 'DangCongTac', '2018-09-01'),
('HADONGGV005', 'Hoàng', 'Em', 'ThS', NULL, 'em.hoang@gv.ptit.edu.vn', '0987654325', 'HADONG', 'VT', 'DangCongTac', '2019-09-01');

-- PhongHoc HADONG
INSERT INTO PhongHoc (MaPhong, TenPhong, ToaNha, Tang, SucChua, LoaiPhong, MaCoSo, TrangThai) VALUES
('PHD001', 'Phòng 101', 'A', 1, 40, 'LyThuyet', 'HADONG', 'HoatDong'),
('PHD002', 'Phòng 102', 'A', 1, 50, 'LyThuyet', 'HADONG', 'HoatDong'),
('PHD003', 'Phòng 201', 'A', 2, 60, 'LyThuyet', 'HADONG', 'HoatDong'),
('PHD004', 'Phòng 301', 'B', 3, 30, 'MayTinh', 'HADONG', 'HoatDong'),
('PHD005', 'Phòng 302', 'B', 3, 30, 'MayTinh', 'HADONG', 'HoatDong'),
('PHD006', 'Hội trường A', 'C', 1, 200, 'HoiTruong', 'HADONG', 'HoatDong');

-- LopHocPhan HADONG
INSERT INTO LopHocPhan (MaLopHP, MaHP, MaHocKy, MaCoSo, MaGV, TenLopHP, SiSoToiDa, SiSoHienTai, HinhThucHoc, TrangThaiLop) VALUES
('CS1001-HADONG-01', 'CS1001', 'HK20251', 'HADONG', 'HADONGGV001', 'CS1001-01', 40, 25, 'Offline', 'Mo'),
('CS1001-HADONG-02', 'CS1001', 'HK20251', 'HADONG', 'HADONGGV002', 'CS1001-02', 50, 30, 'Offline', 'Mo'),
('CS1002-HADONG-01', 'CS1002', 'HK20251', 'HADONG', 'HADONGGV001', 'CS1002-01', 35, 20, 'Offline', 'Mo'),
('CS1003-HADONG-01', 'CS1003', 'HK20251', 'HADONG', 'HADONGGV002', 'CS1003-01', 40, 22, 'Offline', 'Mo'),
('CS1004-HADONG-01', 'CS1004', 'HK20251', 'HADONG', 'HADONGGV003', 'CS1004-01', 40, 18, 'Offline', 'Mo'),
('CS1005-HADONG-01', 'CS1005', 'HK20251', 'HADONG', 'HADONGGV003', 'CS1005-01', 30, 15, 'TuChon', 'Mo'),
('CS1006-HADONG-01', 'CS1006', 'HK20251', 'HADONG', 'HADONGGV001', 'CS1006-01', 35, 20, 'Offline', 'Mo'),
('CS1008-HADONG-01', 'CS1008', 'HK20251', 'HADONG', 'HADONGGV002', 'CS1008-01', 40, 25, 'Offline', 'Mo'),
('CS1009-HADONG-01', 'CS1009', 'HK20251', 'HADONG', 'HADONGGV004', 'CS1009-01', 35, 20, 'Offline', 'Mo'),
('CS1011-HADONG-01', 'CS1011', 'HK20251', 'HADONG', 'HADONGGV003', 'CS1011-01', 40, 22, 'Hybrid', 'Mo');

-- LichHoc HADONG
INSERT INTO LichHoc (MaLich, MaLopHP, MaPhong, ThuTrongTuan, TietBatDau, SoTiet, NgayBatDau, NgayKetThuc) VALUES
('LH001', 'CS1001-HADONG-01', 'PHD001', 2, 1, 3, '2025-09-01', '2025-12-31'),
('LH002', 'CS1001-HADONG-01', 'PHD001', 4, 4, 2, '2025-09-01', '2025-12-31'),
('LH003', 'CS1001-HADONG-02', 'PHD002', 3, 7, 3, '2025-09-01', '2025-12-31'),
('LH004', 'CS1002-HADONG-01', 'PHD003', 2, 4, 4, '2025-09-01', '2025-12-31'),
('LH005', 'CS1003-HADONG-01', 'PHD001', 5, 1, 3, '2025-09-01', '2025-12-31'),
('LH006', 'CS1004-HADONG-01', 'PHD002', 3, 1, 3, '2025-09-01', '2025-12-31'),
('LH007', 'CS1006-HADONG-01', 'PHD003', 6, 7, 3, '2025-09-01', '2025-12-31'),
('LH008', 'CS1008-HADONG-01', 'PHD004', 2, 7, 3, '2025-09-01', '2025-12-31'),
('LH009', 'CS1009-HADONG-01', 'PHD005', 4, 1, 3, '2025-09-01', '2025-12-31'),
('LH010', 'CS1011-HADONG-01', 'PHD006', 7, 1, 4, '2025-09-01', '2025-12-31');

-- SinhVien HADONG (20 mẫu)
INSERT INTO SinhVien (MaSV, Ho, Ten, NgaySinh, GioiTinh, Email, SoDienThoai, DiaChi, MaCoSo, MaKhoa, TrangThai, NgayNhapHoc) VALUES
('HADONGSV0001', 'Nguyễn', 'Vân', '2003-05-15', 'Nu', 'nguyen.van001@ptit.edu.vn', '0981234567', 'Hà Nội', 'HADONG', 'CNTT', 'DangHoc', '2021-09-01'),
('HADONGSV0002', 'Trần', 'Nam', '2003-07-22', 'Nam', 'tran.nam002@ptit.edu.vn', '0981234568', 'Hải Phòng', 'HADONG', 'CNTT', 'DangHoc', '2021-09-01'),
('HADONGSV0003', 'Lê', 'Hương', '2004-01-10', 'Nu', 'le.huong003@ptit.edu.vn', '0981234569', 'Hà Nội', 'HADONG', 'ATTT', 'DangHoc', '2022-09-01'),
('HADONGSV0004', 'Phạm', 'Minh', '2004-03-25', 'Nam', 'pham.minh004@ptit.edu.vn', '0981234570', 'Hà Nam', 'HADONG', 'VT', 'DangHoc', '2022-09-01'),
('HADONGSV0005', 'Hoàng', 'Lan', '2003-11-08', 'Nu', 'hoang.lan005@ptit.edu.vn', '0981234571', 'Bắc Ninh', 'HADONG', 'CNTT', 'DangHoc', '2021-09-01'),
('HADONGSV0006', 'Đặng', 'Anh', '2004-06-17', 'Nam', 'dang.anh006@ptit.edu.vn', '0981234572', 'Hà Nội', 'HADONG', 'KT', 'DangHoc', '2022-09-01'),
('HADONGSV0007', 'Bùi', 'Thảo', '2004-09-30', 'Nu', 'bui.thao007@ptit.edu.vn', '0981234573', 'Hưng Yên', 'HADONG', 'CNTT', 'DangHoc', '2022-09-01'),
('HADONGSV0008', 'Ngô', 'Hùng', '2003-12-05', 'Nam', 'ngo.hung008@ptit.edu.vn', '0981234574', 'Vĩnh Phúc', 'HADONG', 'CNTT', 'DangHoc', '2021-09-01'),
('HADONGSV0009', 'Đỗ', 'Trang', '2004-04-18', 'Nu', 'do.trang009@ptit.edu.vn', '0981234575', 'Hà Nội', 'HADONG', 'ATTT', 'DangHoc', '2022-09-01'),
('HADONGSV0010', 'Trương', 'Dũng', '2004-08-12', 'Nam', 'truong.dung010@ptit.edu.vn', '0981234576', 'Hải Dương', 'HADONG', 'VT', 'DangHoc', '2022-09-01'),
('HADONGSV0011', 'Vũ', 'Linh', '2005-02-20', 'Nu', 'vu.linh011@ptit.edu.vn', '0981234577', 'Hà Nội', 'HADONG', 'CNTT', 'DangHoc', '2023-09-01'),
('HADONGSV0012', 'Đinh', 'Tuấn', '2005-07-14', 'Nam', 'dinh.tuan012@ptit.edu.vn', '0981234578', 'Thái Bình', 'HADONG', 'CNTT', 'DangHoc', '2023-09-01'),
('HADONGSV0013', 'Hồ', 'Mai', '2004-11-25', 'Nu', 'ho.mai013@ptit.edu.vn', '0981234579', 'Nam Định', 'HADONG', 'KT', 'DangHoc', '2022-09-01'),
('HADONGSV0014', 'Lý', 'Phong', '2005-01-03', 'Nam', 'ly.phong014@ptit.edu.vn', '0981234580', 'Hà Nội', 'HADONG', 'CNTT', 'DangHoc', '2023-09-01'),
('HADONGSV0015', 'Mạc', 'Yến', '2004-05-09', 'Nu', 'mac.yen015@ptit.edu.vn', '0981234581', 'Ninh Bình', 'HADONG', 'ATTT', 'DangHoc', '2022-09-01'),
('HADONGSV0016', 'Tạ', 'Hùng', '2005-03-28', 'Nam', 'ta.hung016@ptit.edu.vn', '0981234582', 'Hà Nội', 'HADONG', 'VT', 'DangHoc', '2023-09-01'),
('HADONGSV0017', 'Phan', 'Ngọc', '2004-10-16', 'Nu', 'phan.ngoc017@ptit.edu.vn', '0981234583', 'Hải Hưng', 'HADONG', 'CNTT', 'DangHoc', '2022-09-01'),
('HADONGSV0018', 'Trịnh', 'Sơn', '2005-06-22', 'Nam', 'trinh.son018@ptit.edu.vn', '0981234584', 'Thanh Hóa', 'HADONG', 'CNTT', 'DangHoc', '2023-09-01'),
('HADONGSV0019', 'Cao', 'Thắm', '2004-02-11', 'Nu', 'cao.tham019@ptit.edu.vn', '0981234585', 'Hà Nội', 'HADONG', 'KT', 'BaoLuu', '2022-09-01'),
('HADONGSV0020', 'Vương', 'Kiên', '2005-08-07', 'Nam', 'vuong.kien020@ptit.edu.vn', '0981234586', 'Bắc Giang', 'HADONG', 'CNTT', 'DangHoc', '2023-09-01');
ENDSQL
echo Done.

echo.
echo [5/6] Verifying HADONG data...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaSV, Ho, Ten FROM sinhvien LIMIT 5;"
echo.
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT MaHP, TenHP FROM hocphan LIMIT 3;"

echo.
echo [6/6] Summary...
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT 'SinhVien' as tbl, COUNT(*) FROM sinhvien UNION ALL SELECT 'GiangVien', COUNT(*) FROM giangvien UNION ALL SELECT 'PhongHoc', COUNT(*) FROM phonghoc UNION ALL SELECT 'LopHocPhan', COUNT(*) FROM lophocphan UNION ALL SELECT 'LichHoc', COUNT(*) FROM lichhoc;"

echo.
echo  Done! Vietnamese data should now display correctly.
pause
