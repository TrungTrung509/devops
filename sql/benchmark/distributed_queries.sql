-- BENCHMARK QUERIES - DISTRIBUTED MODEL
-- So sanh voi Centralized

-- QUERY 1: Danh sach lop hoc phan theo co so (LOCAL)
-- Muc tieu: Truy van local, chi doc du lieu tai mot site
-- Phan tan: query truc tiep tai site HADONG (khong can FDW)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    lhp."MaLopHP",
    lhp."MaHP",
    hp."TenHP",
    lhp."SiSoToiDa",
    lhp."SiSoHienTai",
    lhp."TrangThaiLop"
FROM "LopHocPhan" lhp
JOIN "HocPhan" hp ON lhp."MaHP" = hp."MaHP"
WHERE lhp."MaCoSo" = 'HADONG'
ORDER BY lhp."MaLopHP";

-- QUERY 2: Thong ke so sinh vien theo tung co so (GLOBAL)
-- Muc tieu: Tong hop du lieu tu nhieu site, dem theo MaCoSo
-- Phan tan: su dung view FDW
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    "MaCoSo",
    COUNT(*) AS "SoSinhVien"
FROM "vw_sinhvien_toantruong"
GROUP BY "MaCoSo"
ORDER BY "MaCoSo";

-- QUERY 3: Ty le lap day lop hoc phan toan truong (GLOBAL)
-- Muc tieu: Aggregate toan truong, JOIN view FDW voi bang replicated
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    lhp."MaCoSo",
    COUNT(*) AS "TongLop",
    SUM(lhp."SiSoHienTai") AS "TongSV_DK",
    SUM(lhp."SiSoToiDa") AS "TongSucChua",
    ROUND(
        SUM(lhp."SiSoHienTai")::NUMERIC / NULLIF(SUM(lhp."SiSoToiDa"), 0) * 100,
        2
    ) AS "TyLeLopDay_Percent"
FROM "vw_lophocphan_toantruong" lhp
GROUP BY lhp."MaCoSo"
ORDER BY lhp."MaCoSo";

-- QUERY 4: Danh sach sinh vien dang ky cheo co so (GLOBAL JOIN)
-- Muc tieu: Join qua nhieu bang, SV o co so khac dang ky lop o co so khac
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    sv."MaSV",
    sv."Ho" || ' ' || sv."Ten" AS "HoTen",
    sv."MaCoSo" AS "CoSoSV",
    lhp."MaLopHP",
    lhp."MaCoSo" AS "CoSoLop",
    dk."NgayDangKy"
FROM "vw_dangky_toantruong" dk
JOIN "vw_sinhvien_toantruong" sv ON dk."MaSV" = sv."MaSV"
JOIN "vw_lophocphan_toantruong" lhp ON dk."MaLopHP" = lhp."MaLopHP"
WHERE sv."MaCoSo" <> lhp."MaCoSo"
ORDER BY dk."NgayDangKy" DESC
LIMIT 20;

-- QUERY 5: Hoc phan nhieu sinh vien dang ky nhat toan truong (GLOBAL)
-- Muc tieu: Top N aggregate, JOIN replicated + view FDW
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    hp."MaHP",
    hp."TenHP",
    hp."SoTinChi",
    COUNT(dk."MaDangKy") AS "TongSV_DK",
    COUNT(DISTINCT lhp."MaCoSo") AS "SoCoSo_MoLop"
FROM "HocPhan" hp
JOIN "vw_lophocphan_toantruong" lhp ON hp."MaHP" = lhp."MaHP"
JOIN "vw_dangky_toantruong" dk ON lhp."MaLopHP" = dk."MaLopHP"
WHERE dk."TrangThaiDangKy" = 'DaDangKy'
GROUP BY hp."MaHP", hp."TenHP", hp."SoTinChi"
ORDER BY COUNT(dk."MaDangKy") DESC
LIMIT 10;

-- QUERY 6: Kiem tra si so lop (LOCAL SELECT)
-- Muc tieu: Dem so SV da dang ky mot lop hoc phan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    lhp."MaLopHP",
    lhp."TenLopHP",
    lhp."SiSoToiDa",
    lhp."SiSoHienTai",
    COUNT(dk."MaDangKy") AS "SL_DK_HienTai"
FROM "LopHocPhan" lhp
LEFT JOIN "DangKy" dk ON lhp."MaLopHP" = dk."MaLopHP" AND dk."TrangThaiDangKy" = 'DaDangKy'
WHERE lhp."MaCoSo" = 'HADONG'
GROUP BY lhp."MaLopHP", lhp."TenLopHP", lhp."SiSoToiDa", lhp."SiSoHienTai"
ORDER BY lhp."MaLopHP";

-- QUERY 7: Tong hop hoc ky & lop hoc phan (GLOBAL)
-- Muc tieu: Query tren bang replicated + view FDW
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    hk."MaHocKy",
    hk."NamHoc",
    hk."KySo",
    hk."TrangThaiHocKy",
    COUNT(DISTINCT lhp."MaLopHP") AS "TongLopHP",
    COUNT(DISTINCT dk."MaDangKy") AS "TongDangKy"
FROM "HocKy" hk
LEFT JOIN "vw_lophocphan_toantruong" lhp ON hk."MaHocKy" = lhp."MaHocKy"
LEFT JOIN "vw_dangky_toantruong" dk ON lhp."MaLopHP" = dk."MaLopHP" AND dk."TrangThaiDangKy" = 'DaDangKy'
GROUP BY hk."MaHocKy", hk."NamHoc", hk."KySo", hk."TrangThaiHocKy"
ORDER BY hk."NamHoc" DESC, hk."KySo";
