-- =====================================================
-- IMPORT DATA SCRIPT - Từ 3 site vào Centralized DB
-- Database: csdlpt_centralized (port 5435)
-- =====================================================

-- NOTE: Script này chạy sau khi schema đã được tạo

-- Bước 1: Import COMMON tables từ HADONG (chỉ 1 lần)
-- Các bảng này giống nhau ở 3 site nên chỉ import từ HADONG

-- Import CoSo
INSERT INTO "CoSo" 
SELECT * FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaCoSo", "TenCoSo", "DiaChi", "SoDienThoai", "Email", "NgayThanhLap", "TrangThai" FROM "CoSo"'
) AS t(
    "MaCoSo" VARCHAR,
    "TenCoSo" VARCHAR,
    "DiaChi" VARCHAR,
    "SoDienThoai" VARCHAR,
    "Email" VARCHAR,
    "NgayThanhLap" DATE,
    "TrangThai" VARCHAR
);

-- Import users
INSERT INTO "users"
SELECT * FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "userId", "username", "password", "email", "role", "MaCoSo", "status", "NgayTao" FROM "users"'
) AS t(
    "userId" VARCHAR,
    "username" VARCHAR,
    "password" VARCHAR,
    "email" VARCHAR,
    "role" VARCHAR,
    "MaCoSo" VARCHAR,
    "status" VARCHAR,
    "NgayTao" VARCHAR
);

-- Import Khoa
INSERT INTO "Khoa"
SELECT * FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaKhoa", "TenKhoa", "MoTa", "NgayThanhLap", "TrangThai" FROM "Khoa"'
) AS t(
    "MaKhoa" VARCHAR,
    "TenKhoa" VARCHAR,
    "MoTa" VARCHAR,
    "NgayThanhLap" DATE,
    "TrangThai" VARCHAR
);

-- Import HocPhan
INSERT INTO "HocPhan"
SELECT * FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaHP", "TenHP", "SoTinChi", "SoTietLyThuyet", "SoTietThucHanh", "LoaiHocPhan", "MaKhoa", "MoTa", "TrangThai", "NgayTao" FROM "HocPhan"'
) AS t(
    "MaHP" VARCHAR,
    "TenHP" VARCHAR,
    "SoTinChi" INTEGER,
    "SoTietLyThuyet" INTEGER,
    "SoTietThucHanh" INTEGER,
    "LoaiHocPhan" VARCHAR,
    "MaKhoa" VARCHAR,
    "MoTa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import HocKy
INSERT INTO "HocKy"
SELECT * FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaHocKy", "NamHoc", "KySo", "NgayBatDau", "NgayKetThuc", "TrangThaiHocKy" FROM "HocKy"'
) AS t(
    "MaHocKy" VARCHAR,
    "NamHoc" VARCHAR,
    "KySo" INTEGER,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "TrangThaiHocKy" VARCHAR
);

-- Bước 2: Import LOCAL tables từ HADONG
-- Thêm SourceSite để truy vết

-- Import SinhVien từ HADONG
INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", "SourceSite")
SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao" FROM "SinhVien"'
) AS t(
    "MaSV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayNhapHoc" DATE,
    "NgayTao" VARCHAR
);

-- Import GiangVien từ HADONG
INSERT INTO "GiangVien" ("MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", "SourceSite")
SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao" FROM "GiangVien"'
) AS t(
    "MaGV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "HocVi" VARCHAR,
    "HocHam" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayVaoLam" DATE,
    "NgayTao" VARCHAR
);

-- Import PhongHoc từ HADONG
INSERT INTO "PhongHoc" ("MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", "SourceSite")
SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao" FROM "PhongHoc"'
) AS t(
    "MaPhong" VARCHAR,
    "TenPhong" VARCHAR,
    "ToaNha" VARCHAR,
    "Tang" INTEGER,
    "SucChua" INTEGER,
    "LoaiPhong" VARCHAR,
    "MaCoSo" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LopHocPhan từ HADONG
INSERT INTO "LopHocPhan" ("MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", "SourceSite")
SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao" FROM "LopHocPhan"'
) AS t(
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaGV" VARCHAR,
    "TenLopHP" VARCHAR,
    "SiSoToiDa" INTEGER,
    "SiSoHienTai" INTEGER,
    "HinhThucHoc" VARCHAR,
    "TrangThaiLop" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LichHoc từ HADONG
INSERT INTO "LichHoc" ("MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", "SourceSite")
SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu" FROM "LichHoc"'
) AS t(
    "MaLich" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaPhong" VARCHAR,
    "ThuTrongTuan" INTEGER,
    "TietBatDau" INTEGER,
    "SoTiet" INTEGER,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "GhiChu" VARCHAR
);

-- Import DangKy từ HADONG (dùng BIGSERIAL, lưu OriginalMaDangKy)
INSERT INTO "DangKy" ("OriginalMaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", "SourceSite")
SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", 'HADONG'
FROM dblink(
    'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu" FROM "DangKy"'
) AS t(
    "MaDangKy" INTEGER,
    "userId" VARCHAR,
    "MaSV" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "NgayDangKy" TIMESTAMP,
    "TrangThaiDangKy" VARCHAR,
    "LanDangKy" INTEGER,
    "GhiChu" VARCHAR
);

-- Bước 3: Import LOCAL tables từ NGOCTRUC

-- Import SinhVien từ NGOCTRUC
INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", "SourceSite")
SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao" FROM "SinhVien"'
) AS t(
    "MaSV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayNhapHoc" DATE,
    "NgayTao" VARCHAR
);

-- Import GiangVien từ NGOCTRUC
INSERT INTO "GiangVien" ("MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", "SourceSite")
SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao" FROM "GiangVien"'
) AS t(
    "MaGV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "HocVi" VARCHAR,
    "HocHam" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayVaoLam" DATE,
    "NgayTao" VARCHAR
);

-- Import PhongHoc từ NGOCTRUC
INSERT INTO "PhongHoc" ("MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", "SourceSite")
SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao" FROM "PhongHoc"'
) AS t(
    "MaPhong" VARCHAR,
    "TenPhong" VARCHAR,
    "ToaNha" VARCHAR,
    "Tang" INTEGER,
    "SucChua" INTEGER,
    "LoaiPhong" VARCHAR,
    "MaCoSo" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LopHocPhan từ NGOCTRUC
INSERT INTO "LopHocPhan" ("MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", "SourceSite")
SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao" FROM "LopHocPhan"'
) AS t(
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaGV" VARCHAR,
    "TenLopHP" VARCHAR,
    "SiSoToiDa" INTEGER,
    "SiSoHienTai" INTEGER,
    "HinhThucHoc" VARCHAR,
    "TrangThaiLop" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LichHoc từ NGOCTRUC
INSERT INTO "LichHoc" ("MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", "SourceSite")
SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu" FROM "LichHoc"'
) AS t(
    "MaLich" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaPhong" VARCHAR,
    "ThuTrongTuan" INTEGER,
    "TietBatDau" INTEGER,
    "SoTiet" INTEGER,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "GhiChu" VARCHAR
);

-- Import DangKy từ NGOCTRUC
INSERT INTO "DangKy" ("OriginalMaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", "SourceSite")
SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", 'NGOCTRUC'
FROM dblink(
    'host=postgres_ngoctruc port=5432 dbname=csdlpt_ngoctruc user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu" FROM "DangKy"'
) AS t(
    "MaDangKy" INTEGER,
    "userId" VARCHAR,
    "MaSV" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "NgayDangKy" TIMESTAMP,
    "TrangThaiDangKy" VARCHAR,
    "LanDangKy" INTEGER,
    "GhiChu" VARCHAR
);

-- Bước 4: Import LOCAL tables từ HOALAC

-- Import SinhVien từ HOALAC
INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", "SourceSite")
SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao" FROM "SinhVien"'
) AS t(
    "MaSV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayNhapHoc" DATE,
    "NgayTao" VARCHAR
);

-- Import GiangVien từ HOALAC
INSERT INTO "GiangVien" ("MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", "SourceSite")
SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao" FROM "GiangVien"'
) AS t(
    "MaGV" VARCHAR,
    "userId" VARCHAR,
    "Ho" VARCHAR,
    "Ten" VARCHAR,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "HocVi" VARCHAR,
    "HocHam" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayVaoLam" DATE,
    "NgayTao" VARCHAR
);

-- Import PhongHoc từ HOALAC
INSERT INTO "PhongHoc" ("MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", "SourceSite")
SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao" FROM "PhongHoc"'
) AS t(
    "MaPhong" VARCHAR,
    "TenPhong" VARCHAR,
    "ToaNha" VARCHAR,
    "Tang" INTEGER,
    "SucChua" INTEGER,
    "LoaiPhong" VARCHAR,
    "MaCoSo" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LopHocPhan từ HOALAC
INSERT INTO "LopHocPhan" ("MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", "SourceSite")
SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao" FROM "LopHocPhan"'
) AS t(
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "MaCoSo" VARCHAR,
    "MaGV" VARCHAR,
    "TenLopHP" VARCHAR,
    "SiSoToiDa" INTEGER,
    "SiSoHienTai" INTEGER,
    "HinhThucHoc" VARCHAR,
    "TrangThaiLop" VARCHAR,
    "NgayTao" TIMESTAMP
);

-- Import LichHoc từ HOALAC
INSERT INTO "LichHoc" ("MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", "SourceSite")
SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu" FROM "LichHoc"'
) AS t(
    "MaLich" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaPhong" VARCHAR,
    "ThuTrongTuan" INTEGER,
    "TietBatDau" INTEGER,
    "SoTiet" INTEGER,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "GhiChu" VARCHAR
);

-- Import DangKy từ HOALAC
INSERT INTO "DangKy" ("OriginalMaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", "SourceSite")
SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu", 'HOALAC'
FROM dblink(
    'host=postgres_hoalac port=5432 dbname=csdlpt_hoalac user=csdlpt_user password=csdlpt_pass',
    'SELECT "MaDangKy", "userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy", "GhiChu" FROM "DangKy"'
) AS t(
    "MaDangKy" INTEGER,
    "userId" VARCHAR,
    "MaSV" VARCHAR,
    "MaLopHP" VARCHAR,
    "MaHP" VARCHAR,
    "MaHocKy" VARCHAR,
    "NgayDangKy" TIMESTAMP,
    "TrangThaiDangKy" VARCHAR,
    "LanDangKy" INTEGER,
    "GhiChu" VARCHAR
);

-- Bước 5: Cập nhật sequence cho DangKy sau khi import
SELECT setval('"DangKy_MaDangKy_seq"', (SELECT COALESCE(MAX("MaDangKy"), 0) FROM "DangKy"));

-- Bước 6: Log kết quả import
SELECT 'Import completed!' AS status;
SELECT 'CoSo' AS tbl, COUNT(*) AS cnt FROM "CoSo"
UNION ALL SELECT 'users', COUNT(*) FROM "users"
UNION ALL SELECT 'Khoa', COUNT(*) FROM "Khoa"
UNION ALL SELECT 'HocPhan', COUNT(*) FROM "HocPhan"
UNION ALL SELECT 'HocKy', COUNT(*) FROM "HocKy"
UNION ALL SELECT 'SinhVien', COUNT(*) FROM "SinhVien"
UNION ALL SELECT 'GiangVien', COUNT(*) FROM "GiangVien"
UNION ALL SELECT 'PhongHoc', COUNT(*) FROM "PhongHoc"
UNION ALL SELECT 'LopHocPhan', COUNT(*) FROM "LopHocPhan"
UNION ALL SELECT 'LichHoc', COUNT(*) FROM "LichHoc"
UNION ALL SELECT 'DangKy', COUNT(*) FROM "DangKy";
