CREATE OR REPLACE VIEW vw_sinhvien_toantruong AS
SELECT * FROM "SinhVien"
UNION ALL
SELECT * FROM fdw_hadong."SinhVien"
UNION ALL
SELECT * FROM fdw_hoalac."SinhVien";

CREATE OR REPLACE VIEW vw_giangvien_toantruong AS
SELECT * FROM "GiangVien"
UNION ALL
SELECT * FROM fdw_hadong."GiangVien"
UNION ALL
SELECT * FROM fdw_hoalac."GiangVien";

CREATE OR REPLACE VIEW vw_phonghoc_toantruong AS
SELECT * FROM "PhongHoc"
UNION ALL
SELECT * FROM fdw_hadong."PhongHoc"
UNION ALL
SELECT * FROM fdw_hoalac."PhongHoc";

CREATE OR REPLACE VIEW vw_lophocphan_toantruong AS
SELECT * FROM "LopHocPhan"
UNION ALL
SELECT * FROM fdw_hadong."LopHocPhan"
UNION ALL
SELECT * FROM fdw_hoalac."LopHocPhan";

CREATE OR REPLACE VIEW vw_lichhoc_toantruong AS
SELECT * FROM "LichHoc"
UNION ALL
SELECT * FROM fdw_hadong."LichHoc"
UNION ALL
SELECT * FROM fdw_hoalac."LichHoc";

CREATE OR REPLACE VIEW vw_dangky_toantruong AS
SELECT * FROM "DangKy"
UNION ALL
SELECT * FROM fdw_hadong."DangKy"
UNION ALL
SELECT * FROM fdw_hoalac."DangKy";
