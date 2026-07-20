
-- CƠ SỞ DỮ LIỆU PHÂN TÁN - ĐỀ TÀI: ĐĂNG KÝ HỌC PHẦN
-- Tác giả: Nhóm CSDL Phân Tán
-- Mô tả: Indexes cho tất cả các bảng
-- Chạy SAU khi đã tạo tất cả bảng

-- INDEXES CHO BẢNG COMMON (chạy tại tất cả site)

-- Index cho HocPhan theo Khoa (JOIN)
CREATE INDEX IF NOT EXISTS idx_hocphan_makhoa ON "HocPhan"("MaKhoa");

-- Index cho HocPhan theo trạng thái (lọc)
CREATE INDEX IF NOT EXISTS idx_hocphan_trangthai ON "HocPhan"("TrangThai");

-- Index cho HocPhan theo loại (lọc)
CREATE INDEX IF NOT EXISTS idx_hocphan_loai ON "HocPhan"("LoaiHocPhan");

-- INDEXES CHO BẢNG users (Common - tìm kiếm & auth)

-- Index cho username (login)
CREATE INDEX IF NOT EXISTS idx_users_username ON "users"("username");

-- Index cho email (tra cứu, validation)
CREATE INDEX IF NOT EXISTS idx_users_email ON "users"("email");

-- Index cho role (lọc theo loại user)
CREATE INDEX IF NOT EXISTS idx_users_role ON "users"("role");

-- Index cho MaCoSo (định tuyến theo cơ sở)
CREATE INDEX IF NOT EXISTS idx_users_macoso ON "users"("MaCoSo");

-- Index cho status (lọc user active/inactive/locked)
CREATE INDEX IF NOT EXISTS idx_users_status ON "users"("status");

-- INDEXES CHO BẢNG LOCAL

-- ---- SinhVien ----
-- Index theo cơ sở (phân mảnh)
CREATE INDEX IF NOT EXISTS idx_sinhvien_macoso ON "SinhVien"("MaCoSo");

-- Index theo khoa (JOIN với Khoa)
CREATE INDEX IF NOT EXISTS idx_sinhvien_makhoa ON "SinhVien"("MaKhoa");

-- Index theo trạng thái (lọc sinh viên đang học)
CREATE INDEX IF NOT EXISTS idx_sinhvien_trangthai ON "SinhVien"("TrangThai");

-- Index theo userId (FK lookup)
CREATE INDEX IF NOT EXISTS idx_sinhvien_userid ON "SinhVien"("userId");

-- ---- GiangVien ----
-- Index theo cơ sở (phân mảnh)
CREATE INDEX IF NOT EXISTS idx_giangvien_macoso ON "GiangVien"("MaCoSo");

-- Index theo khoa (JOIN)
CREATE INDEX IF NOT EXISTS idx_giangvien_makhoa ON "GiangVien"("MaKhoa");

-- Index theo trạng thái
CREATE INDEX IF NOT EXISTS idx_giangvien_trangthai ON "GiangVien"("TrangThai");

-- Index theo userId (FK lookup)
CREATE INDEX IF NOT EXISTS idx_giangvien_userid ON "GiangVien"("userId");

-- ---- PhongHoc ----
-- Index theo cơ sở (phân mảnh)
CREATE INDEX IF NOT EXISTS idx_phonghoc_macoso ON "PhongHoc"("MaCoSo");

-- Index theo loại phòng (lọc)
CREATE INDEX IF NOT EXISTS idx_phonghoc_loai ON "PhongHoc"("LoaiPhong");

-- Index theo trạng thái (phòng đang hoạt động)
CREATE INDEX IF NOT EXISTS idx_phonghoc_trangthai ON "PhongHoc"("TrangThai");

-- ---- LopHocPhan ----
-- Index theo học phần (JOIN với HocPhan)
CREATE INDEX IF NOT EXISTS idx_lophocphan_mahp ON "LopHocPhan"("MaHP");

-- Index theo học kỳ (lọc theo kỳ)
CREATE INDEX IF NOT EXISTS idx_lophocphan_mahocky ON "LopHocPhan"("MaHocKy");

-- Index theo cơ sở mở lớp (phân mảnh)
CREATE INDEX IF NOT EXISTS idx_lophocphan_macoso ON "LopHocPhan"("MaCoSo");

-- Index theo giảng viên (JOIN)
CREATE INDEX IF NOT EXISTS idx_lophocphan_magv ON "LopHocPhan"("MaGV");

-- Index theo trạng thái (lớp đang mở)
CREATE INDEX IF NOT EXISTS idx_lophocphan_trangthai ON "LopHocPhan"("TrangThaiLop");

-- Index tổ hợp: Học phần + Học kỳ + Cơ sở (tra cứu nhanh)
CREATE INDEX IF NOT EXISTS idx_lophocphan_hp_hk_cs ON "LopHocPhan"("MaHP", "MaHocKy", "MaCoSo");

-- Index cho kiểm tra sĩ số (SiSoHienTai vs SiSoToiDa)
CREATE INDEX IF NOT EXISTS idx_lophocphan_siso ON "LopHocPhan"("SiSoHienTai", "SiSoToiDa");

-- ---- LichHoc ----
-- Index theo lớp học phần (JOIN, phân mảnh dẫn xuất)
CREATE INDEX IF NOT EXISTS idx_lichhoc_malophp ON "LichHoc"("MaLopHP");

-- Index theo phòng (kiểm tra trùng phòng)
CREATE INDEX IF NOT EXISTS idx_lichhoc_maphong ON "LichHoc"("MaPhong");

-- Index tổ hợp: Phòng + Thứ + Tiết (kiểm tra trùng lịch phòng)
CREATE INDEX IF NOT EXISTS idx_lichhoc_phong_thu_tiet ON "LichHoc"("MaPhong", "ThuTrongTuan", "TietBatDau");

-- Index theo thời gian
CREATE INDEX IF NOT EXISTS idx_lichhoc_ngay ON "LichHoc"("NgayBatDau", "NgayKetThuc");

-- ---- DangKy ----
-- Index theo userId (tra cứu đăng ký của user - khớp với Enrollment.userId FK)
-- MaSV là nullable, chỉ dùng để in ấn. Query chính dùng userId.
CREATE INDEX IF NOT EXISTS idx_dangky_userid ON "DangKy"("userId");

-- Index theo lớp học phần (tra cứu SV đăng ký lớp)
CREATE INDEX IF NOT EXISTS idx_dangky_malophp ON "DangKy"("MaLopHP");

-- Index theo trạng thái (lọc đăng ký đang hiệu lực)
CREATE INDEX IF NOT EXISTS idx_dangky_trangthai ON "DangKy"("TrangThaiDangKy");

-- Index tổ hợp: userId + MaHP + MaHocKy (khớp với UniqueConstraint trong Enrollment model)
CREATE INDEX IF NOT EXISTS idx_dangky_userid_hp_hk ON "DangKy"("userId", "MaHP", "MaHocKy");

-- Index để đếm sĩ số nhanh
CREATE INDEX IF NOT EXISTS idx_dangky_demsiso ON "DangKy"("MaLopHP") WHERE "TrangThaiDangKy" = 'DaDangKy';

-- INDEXES CHO REPLICATION & FDW (chạy tại tất cả site)

-- Index cho HocKy theo năm học
CREATE INDEX IF NOT EXISTS idx_hocky_namhoc ON "HocKy"("NamHoc");

-- INDEXES CHO PERFORMANCE (chạy tại site HADONG - publisher)

-- Index cho Khoa theo trạng thái
CREATE INDEX IF NOT EXISTS idx_khoa_trangthai ON "Khoa"("TrangThai");

-- Index cho CoSo theo trạng thái
CREATE INDEX IF NOT EXISTS idx_coso_trangthai ON "CoSo"("TrangThai");

-- GHI CHÚ
-- Các index trên hỗ trợ:
-- 1. JOIN giữa các bảng (FK)
-- 2. Phân mảnh dữ liệu (WHERE theo MaCoSo)
-- 3. Kiểm tra ràng buộc nghiệp vụ (trùng lịch, trùng đăng ký, sĩ số)
-- 4. Tối ưu truy vấn phân tán (qua FDW)
