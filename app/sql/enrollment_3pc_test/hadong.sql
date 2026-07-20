BEGIN;

INSERT INTO "HocKy" ("MaHocKy", "NamHoc", "KySo", "NgayBatDau", "NgayKetThuc", "TrangThaiHocKy")
VALUES
    ('20241', '2024-2025', 1, DATE '2024-08-15', DATE '2024-12-20', 'DangDangKy')
ON CONFLICT ("MaHocKy") DO UPDATE
SET "NamHoc" = EXCLUDED."NamHoc",
    "KySo" = EXCLUDED."KySo",
    "NgayBatDau" = EXCLUDED."NgayBatDau",
    "NgayKetThuc" = EXCLUDED."NgayKetThuc",
    "TrangThaiHocKy" = EXCLUDED."TrangThaiHocKy";

INSERT INTO "HocPhan" ("MaHP", "TenHP", "SoTinChi", "SoTietLyThuyet", "SoTietThucHanh", "LoaiHocPhan", "MaKhoa", "MoTa", "TrangThai", "NgayTao")
VALUES
    ('INT1306', 'Nhap mon co so du lieu phan tan', 3, 30, 15, 'BatBuoc', 'CNTT', 'Hoc phan dung de test dang ky 3PC', 'HoatDong', NOW())
ON CONFLICT ("MaHP") DO UPDATE
SET "TenHP" = EXCLUDED."TenHP",
    "SoTinChi" = EXCLUDED."SoTinChi",
    "SoTietLyThuyet" = EXCLUDED."SoTietLyThuyet",
    "SoTietThucHanh" = EXCLUDED."SoTietThucHanh",
    "LoaiHocPhan" = EXCLUDED."LoaiHocPhan",
    "MaKhoa" = EXCLUDED."MaKhoa",
    "MoTa" = EXCLUDED."MoTa",
    "TrangThai" = EXCLUDED."TrangThai";

INSERT INTO "users" ("userId", "username", "password", "email", "role", "MaCoSo", "status", "NgayTao")
VALUES
    ('SV001', 'SV001', '$2b$12$oeR.zwHjExAfSktTRygaA.r7JmAULUIwQDE2/3I4YVvHT6OJ5YSUq', 'sv001@ptit.local', 'SinhVien', 'HADONG', 'Active', NOW()::text),
    ('GVHD01', 'GVHD01', '$2b$12$jZBsJZgEc3lntqcWP1MfI.iOYyWf4TWsZTWiqv7pIgUhpIZKnVRmC', 'gvhd01@ptit.local', 'GiangVien', 'HADONG', 'Active', NOW()::text)
ON CONFLICT ("userId") DO UPDATE
SET "username" = EXCLUDED."username",
    "password" = EXCLUDED."password",
    "email" = EXCLUDED."email",
    "role" = EXCLUDED."role",
    "MaCoSo" = EXCLUDED."MaCoSo",
    "status" = EXCLUDED."status";

INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao")
VALUES
    ('SV001', 'SV001', 'Nguyen', 'SinhVienTest', DATE '2004-01-15', 'Nam', '0900000001', 'Ha Dong, Ha Noi', 'HADONG', 'CNTT', 'DangHoc', DATE '2022-09-01', NOW()::text)
ON CONFLICT ("MaSV") DO UPDATE
SET "Ho" = EXCLUDED."Ho",
    "Ten" = EXCLUDED."Ten",
    "NgaySinh" = EXCLUDED."NgaySinh",
    "GioiTinh" = EXCLUDED."GioiTinh",
    "SDT" = EXCLUDED."SDT",
    "DiaChi" = EXCLUDED."DiaChi",
    "MaCoSo" = EXCLUDED."MaCoSo",
    "MaKhoa" = EXCLUDED."MaKhoa",
    "TrangThai" = EXCLUDED."TrangThai",
    "NgayNhapHoc" = EXCLUDED."NgayNhapHoc";

INSERT INTO "GiangVien" ("MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao")
VALUES
    ('GVHD01', 'GVHD01', 'Tran', 'GiangVienHaDong', DATE '1985-05-20', 'Nam', 'ThacSi', 'GiangVien', '0901000001', 'Ha Dong, Ha Noi', 'HADONG', 'CNTT', 'DangCongTac', DATE '2015-09-01', NOW()::text)
ON CONFLICT ("MaGV") DO UPDATE
SET "userId" = EXCLUDED."userId",
    "Ho" = EXCLUDED."Ho",
    "Ten" = EXCLUDED."Ten",
    "NgaySinh" = EXCLUDED."NgaySinh",
    "GioiTinh" = EXCLUDED."GioiTinh",
    "HocVi" = EXCLUDED."HocVi",
    "HocHam" = EXCLUDED."HocHam",
    "SDT" = EXCLUDED."SDT",
    "DiaChi" = EXCLUDED."DiaChi",
    "MaCoSo" = EXCLUDED."MaCoSo",
    "MaKhoa" = EXCLUDED."MaKhoa",
    "TrangThai" = EXCLUDED."TrangThai",
    "NgayVaoLam" = EXCLUDED."NgayVaoLam";

INSERT INTO "PhongHoc" ("MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao")
VALUES
    ('HD-P101', 'Phong P101 Ha Dong', 'A1', 1, 60, 'LyThuyet', 'HADONG', 'HoatDong', NOW())
ON CONFLICT ("MaPhong") DO UPDATE
SET "TenPhong" = EXCLUDED."TenPhong",
    "ToaNha" = EXCLUDED."ToaNha",
    "Tang" = EXCLUDED."Tang",
    "SucChua" = EXCLUDED."SucChua",
    "LoaiPhong" = EXCLUDED."LoaiPhong",
    "MaCoSo" = EXCLUDED."MaCoSo",
    "TrangThai" = EXCLUDED."TrangThai";

INSERT INTO "LopHocPhan" ("MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao")
VALUES
    ('INT1306_HD01', 'INT1306', '20241', 'HADONG', 'GVHD01', 'INT1306 - Ha Dong - 01', 50, 0, 'Offline', 'Mo', NOW())
ON CONFLICT ("MaLopHP") DO UPDATE
SET "MaHP" = EXCLUDED."MaHP",
    "MaHocKy" = EXCLUDED."MaHocKy",
    "MaCoSo" = EXCLUDED."MaCoSo",
    "MaGV" = EXCLUDED."MaGV",
    "TenLopHP" = EXCLUDED."TenLopHP",
    "SiSoToiDa" = EXCLUDED."SiSoToiDa",
    "HinhThucHoc" = EXCLUDED."HinhThucHoc",
    "TrangThaiLop" = EXCLUDED."TrangThaiLop";

INSERT INTO "LichHoc" ("MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu")
VALUES
    ('INT1306_HD01_L1', 'INT1306_HD01', 'HD-P101', 2, 1, 3, DATE '2024-08-19', DATE '2024-12-16', 'Lich test Ha Dong')
ON CONFLICT ("MaLich") DO UPDATE
SET "MaLopHP" = EXCLUDED."MaLopHP",
    "MaPhong" = EXCLUDED."MaPhong",
    "ThuTrongTuan" = EXCLUDED."ThuTrongTuan",
    "TietBatDau" = EXCLUDED."TietBatDau",
    "SoTiet" = EXCLUDED."SoTiet",
    "NgayBatDau" = EXCLUDED."NgayBatDau",
    "NgayKetThuc" = EXCLUDED."NgayKetThuc",
    "GhiChu" = EXCLUDED."GhiChu";

COMMIT;
