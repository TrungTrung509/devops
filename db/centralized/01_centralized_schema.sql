-- =====================================================
-- CENTRALIZED DATABASE SCHEMA
-- Database: csdlpt_centralized (port 5435)
-- Mô hình tập trung: tất cả dữ liệu 3 site gom về 1 DB
-- =====================================================

-- COMMON TABLES (nhân bản từ 3 site, lấy từ HADONG một lần)
-- Các bảng này giống nhau ở cả 3 site

CREATE TABLE "CoSo" (
    "MaCoSo" VARCHAR NOT NULL PRIMARY KEY,
    "TenCoSo" VARCHAR NOT NULL,
    "DiaChi" VARCHAR,
    "SoDienThoai" VARCHAR,
    "Email" VARCHAR,
    "NgayThanhLap" DATE,
    "TrangThai" VARCHAR
);

CREATE TABLE "users" (
    "userId" VARCHAR NOT NULL PRIMARY KEY,
    "username" VARCHAR NOT NULL UNIQUE,
    "password" VARCHAR NOT NULL,
    "email" VARCHAR NOT NULL UNIQUE,
    "role" VARCHAR NOT NULL,
    "MaCoSo" VARCHAR NOT NULL,
    "status" VARCHAR,
    "NgayTao" VARCHAR
);

CREATE TABLE "Khoa" (
    "MaKhoa" VARCHAR NOT NULL PRIMARY KEY,
    "TenKhoa" VARCHAR NOT NULL UNIQUE,
    "MoTa" VARCHAR,
    "NgayThanhLap" DATE,
    "TrangThai" VARCHAR
);

CREATE TABLE "HocPhan" (
    "MaHP" VARCHAR NOT NULL PRIMARY KEY,
    "TenHP" VARCHAR NOT NULL,
    "SoTinChi" INTEGER NOT NULL,
    "SoTietLyThuyet" INTEGER NOT NULL,
    "SoTietThucHanh" INTEGER NOT NULL,
    "LoaiHocPhan" VARCHAR NOT NULL,
    "MaKhoa" VARCHAR NOT NULL,
    "MoTa" VARCHAR,
    "TrangThai" VARCHAR NOT NULL,
    "NgayTao" TIMESTAMP NOT NULL,
    CONSTRAINT "HocPhan_MaKhoa_fkey" FOREIGN KEY ("MaKhoa") REFERENCES "Khoa"("MaKhoa")
);

CREATE TABLE "HocKy" (
    "MaHocKy" VARCHAR NOT NULL PRIMARY KEY,
    "NamHoc" VARCHAR NOT NULL,
    "KySo" INTEGER NOT NULL,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "TrangThaiHocKy" VARCHAR NOT NULL
);

-- LOCAL TABLES (dữ liệu từ 3 site, thêm SourceSite để truy vết)

CREATE TABLE "SinhVien" (
    "MaSV" VARCHAR NOT NULL PRIMARY KEY,
    "userId" VARCHAR NOT NULL,
    "Ho" VARCHAR NOT NULL,
    "Ten" VARCHAR NOT NULL,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR NOT NULL,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayNhapHoc" DATE,
    "NgayTao" VARCHAR,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    CONSTRAINT "SinhVien_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("userId")
);

CREATE TABLE "GiangVien" (
    "MaGV" VARCHAR NOT NULL PRIMARY KEY,
    "userId" VARCHAR NOT NULL,
    "Ho" VARCHAR NOT NULL,
    "Ten" VARCHAR NOT NULL,
    "NgaySinh" DATE,
    "GioiTinh" VARCHAR,
    "HocVi" VARCHAR,
    "HocHam" VARCHAR,
    "SDT" VARCHAR,
    "DiaChi" VARCHAR,
    "MaCoSo" VARCHAR NOT NULL,
    "MaKhoa" VARCHAR,
    "TrangThai" VARCHAR,
    "NgayVaoLam" DATE,
    "NgayTao" VARCHAR,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    CONSTRAINT "GiangVien_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("userId")
);

CREATE TABLE "PhongHoc" (
    "MaPhong" VARCHAR NOT NULL PRIMARY KEY,
    "TenPhong" VARCHAR,
    "ToaNha" VARCHAR,
    "Tang" INTEGER,
    "SucChua" INTEGER,
    "LoaiPhong" VARCHAR,
    "MaCoSo" VARCHAR NOT NULL,
    "TrangThai" VARCHAR,
    "NgayTao" TIMESTAMP NOT NULL,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN'
);

CREATE TABLE "LopHocPhan" (
    "MaLopHP" VARCHAR NOT NULL PRIMARY KEY,
    "MaHP" VARCHAR NOT NULL,
    "MaHocKy" VARCHAR NOT NULL,
    "MaCoSo" VARCHAR NOT NULL,
    "MaGV" VARCHAR NOT NULL,
    "TenLopHP" VARCHAR,
    "SiSoToiDa" INTEGER NOT NULL,
    "SiSoHienTai" INTEGER NOT NULL DEFAULT 0,
    "HinhThucHoc" VARCHAR NOT NULL,
    "TrangThaiLop" VARCHAR NOT NULL,
    "NgayTao" TIMESTAMP NOT NULL,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    CONSTRAINT "LopHocPhan_MaCoSo_fkey" FOREIGN KEY ("MaCoSo") REFERENCES "CoSo"("MaCoSo"),
    CONSTRAINT "LopHocPhan_MaHP_fkey" FOREIGN KEY ("MaHP") REFERENCES "HocPhan"("MaHP"),
    CONSTRAINT "LopHocPhan_MaHocKy_fkey" FOREIGN KEY ("MaHocKy") REFERENCES "HocKy"("MaHocKy"),
    CONSTRAINT "LopHocPhan_MaGV_fkey" FOREIGN KEY ("MaGV") REFERENCES "GiangVien"("MaGV")
);

CREATE TABLE "LichHoc" (
    "MaLich" VARCHAR NOT NULL PRIMARY KEY,
    "MaLopHP" VARCHAR NOT NULL,
    "MaPhong" VARCHAR NOT NULL,
    "ThuTrongTuan" INTEGER NOT NULL,
    "TietBatDau" INTEGER NOT NULL,
    "SoTiet" INTEGER NOT NULL,
    "NgayBatDau" DATE,
    "NgayKetThuc" DATE,
    "GhiChu" VARCHAR,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    CONSTRAINT "LichHoc_MaPhong_fkey" FOREIGN KEY ("MaPhong") REFERENCES "PhongHoc"("MaPhong"),
    CONSTRAINT "LichHoc_MaLopHP_fkey" FOREIGN KEY ("MaLopHP") REFERENCES "LopHocPhan"("MaLopHP")
);

-- DangKy: Thêm SourceSite và OriginalMaDangKy để tránh trùng SERIAL
CREATE TABLE "DangKy" (
    "MaDangKy" BIGSERIAL NOT NULL PRIMARY KEY,
    "OriginalMaDangKy" INTEGER,
    "userId" VARCHAR NOT NULL,
    "MaSV" VARCHAR,
    "MaLopHP" VARCHAR NOT NULL,
    "MaHP" VARCHAR NOT NULL,
    "MaHocKy" VARCHAR NOT NULL,
    "NgayDangKy" TIMESTAMP NOT NULL,
    "TrangThaiDangKy" VARCHAR NOT NULL,
    "LanDangKy" INTEGER NOT NULL,
    "GhiChu" VARCHAR,
    "SourceSite" VARCHAR NOT NULL DEFAULT 'UNKNOWN',
    CONSTRAINT "DangKy_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("userId"),
    CONSTRAINT "DangKy_MaHP_fkey" FOREIGN KEY ("MaHP") REFERENCES "HocPhan"("MaHP"),
    CONSTRAINT "DangKy_MaHocKy_fkey" FOREIGN KEY ("MaHocKy") REFERENCES "HocKy"("MaHocKy"),
    CONSTRAINT "DangKy_MaLopHP_fkey" FOREIGN KEY ("MaLopHP") REFERENCES "LopHocPhan"("MaLopHP"),
    UNIQUE ("userId", "MaHP", "MaHocKy")
);

-- AUDIT/TRANSACTION TABLES

CREATE TABLE "DangKy_3PC" (
    "RecordId" SERIAL NOT NULL PRIMARY KEY,
    "TxnId" VARCHAR NOT NULL,
    "CoordinatorSite" VARCHAR NOT NULL,
    "SiteId" VARCHAR NOT NULL,
    "UserId" VARCHAR NOT NULL,
    "Action" VARCHAR NOT NULL,
    "State" VARCHAR NOT NULL,
    "TargetMaLopHP" VARCHAR NOT NULL,
    "TargetMaHP" VARCHAR NOT NULL,
    "TargetMaHocKy" VARCHAR NOT NULL,
    "OldMaLopHP" VARCHAR,
    "Payload" TEXT NOT NULL,
    "Message" TEXT,
    "CreatedAt" TIMESTAMP NOT NULL,
    "UpdatedAt" TIMESTAMP NOT NULL
);

CREATE TABLE "DangKy_ChuyenCoSo" (
    "Id" SERIAL NOT NULL PRIMARY KEY,
    "userId" VARCHAR NOT NULL,
    "MaLopHP" VARCHAR NOT NULL,
    "MaHP" VARCHAR NOT NULL,
    "TargetSite" VARCHAR NOT NULL,
    "Timestamp" TIMESTAMP NOT NULL,
    CONSTRAINT "DangKy_ChuyenCoSo_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("userId")
);

CREATE TABLE "NhatKyPhucHoi" (
    "LogId" SERIAL NOT NULL PRIMARY KEY,
    "TxnId" VARCHAR NOT NULL,
    "userId" VARCHAR,
    "MaLopHP" VARCHAR,
    "Action" VARCHAR NOT NULL,
    "MaCoSo" VARCHAR,
    "Status" VARCHAR,
    "Message" TEXT,
    "Timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE "NhatKyThaoTac" (
    "ID" SERIAL NOT NULL PRIMARY KEY,
    "userId" VARCHAR,
    "Action" VARCHAR NOT NULL,
    "TableName" VARCHAR,
    "RecordId" VARCHAR,
    "OldData" TEXT,
    "NewData" TEXT,
    "Timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE "ReplicationOutbox" (
    "EventId" SERIAL NOT NULL PRIMARY KEY,
    "EntityType" VARCHAR NOT NULL,
    "EntityId" VARCHAR NOT NULL,
    "Operation" VARCHAR NOT NULL,
    "Payload" TEXT NOT NULL,
    "SourceSite" VARCHAR NOT NULL,
    "TargetSite" VARCHAR NOT NULL,
    "Status" VARCHAR NOT NULL,
    "RetryCount" INTEGER NOT NULL DEFAULT 0,
    "LastError" TEXT,
    "CreatedAt" TIMESTAMP NOT NULL,
    "UpdatedAt" TIMESTAMP NOT NULL,
    "ProcessedAt" TIMESTAMP
);

CREATE TABLE "SiteStatus" (
    "SiteId" VARCHAR NOT NULL PRIMARY KEY,
    "Role" VARCHAR NOT NULL,
    "Status" VARCHAR NOT NULL,
    "LastHeartbeat" TIMESTAMP,
    "LastSuccessAt" TIMESTAMP,
    "LastError" TEXT,
    "UpdatedAt" TIMESTAMP NOT NULL
);

-- INDEXES for performance
CREATE INDEX idx_lophocphan_macosO ON "LopHocPhan"("MaCoSo");
CREATE INDEX idx_sinhvien_macosO ON "SinhVien"("MaCoSo");
CREATE INDEX idx_giangvien_macosO ON "GiangVien"("MaCoSo");
CREATE INDEX idx_phonghoc_macosO ON "PhongHoc"("MaCoSo");
CREATE INDEX idx_lichhoc_malophp ON "LichHoc"("MaLopHP");
CREATE INDEX idx_dangky_masv ON "DangKy"("MaSV");
CREATE INDEX idx_dangky_malophp ON "DangKy"("MaLopHP");
CREATE INDEX idx_dangky_sourceSite ON "DangKy"("SourceSite");
CREATE INDEX idx_lophocphan_sourceSite ON "LopHocPhan"("SourceSite");
CREATE INDEX idx_sinhvien_sourceSite ON "SinhVien"("SourceSite");

-- COMMENTS
COMMENT ON TABLE "CoSo" IS 'Bảng cơ sở - replicated từ 3 site';
COMMENT ON TABLE "users" IS 'Bảng người dùng - replicated từ 3 site';
COMMENT ON TABLE "SinhVien" IS 'Bảng sinh viên - local table từ 3 site, thêm SourceSite';
COMMENT ON TABLE "DangKy" IS 'Bảng đăng ký - local table từ 3 site, dùng BIGSERIAL để tránh trùng';
