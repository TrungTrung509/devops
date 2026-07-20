-- Distributed report queries
-- Cach dung:
-- 1) Ket noi vao mot site da co FDW + view, vi du HADONG.
-- 2) Neu can loc theo hoc ky, thay NULL trong CTE params bang ma hoc ky, vi du 'HK20251'.

-- 1. Thong ke so sinh vien dang ky hoc phan theo tung co so
WITH params AS (
    SELECT NULL::text AS ma_hk
)
SELECT
    sv."MaCoSo" AS "MaCoSo",
    cs."TenCoSo" AS "TenCoSo",
    COUNT(DISTINCT dk."MaSV") AS "SoSinhVienDangKy",
    COUNT(*) AS "SoLuotDangKy"
FROM vw_dangky_toantruong dk
JOIN vw_sinhvien_toantruong sv
    ON sv."MaSV" = dk."MaSV"
LEFT JOIN "CoSo" cs
    ON cs."MaCoSo" = sv."MaCoSo"
CROSS JOIN params p
WHERE dk."TrangThaiDangKy" = 'DaDangKy'
  AND (p.ma_hk IS NULL OR dk."MaHocKy" = p.ma_hk)
GROUP BY sv."MaCoSo", cs."TenCoSo"
ORDER BY sv."MaCoSo";


-- 2. Tim hoc phan co nhieu sinh vien dang ky nhat toan truong
WITH params AS (
    SELECT NULL::text AS ma_hk
),
ranked_courses AS (
    SELECT
        hp."MaHP" AS "MaHP",
        hp."TenHP" AS "TenHocPhan",
        hp."MaKhoa" AS "MaKhoa",
        COUNT(DISTINCT dk."MaSV") AS "SoSinhVienDangKy",
        COUNT(*) AS "SoLuotDangKy",
        RANK() OVER (
            ORDER BY COUNT(DISTINCT dk."MaSV") DESC, COUNT(*) DESC
        ) AS ranking
    FROM vw_dangky_toantruong dk
    JOIN "HocPhan" hp
        ON hp."MaHP" = dk."MaHP"
    CROSS JOIN params p
    WHERE dk."TrangThaiDangKy" = 'DaDangKy'
      AND (p.ma_hk IS NULL OR dk."MaHocKy" = p.ma_hk)
    GROUP BY hp."MaHP", hp."TenHP", hp."MaKhoa"
)
SELECT
    "MaHP",
    "TenHocPhan",
    "MaKhoa",
    "SoSinhVienDangKy",
    "SoLuotDangKy"
FROM ranked_courses
WHERE ranking = 1
ORDER BY "MaHP";


-- 3. Danh sach sinh vien dang ky cheo co so
WITH params AS (
    SELECT NULL::text AS ma_hk
)
SELECT
    sv."MaSV" AS "MaSV",
    TRIM(COALESCE(sv."Ho", '') || ' ' || COALESCE(sv."Ten", '')) AS "HoTen",
    sv."MaCoSo" AS "CoSoSinhVien",
    dk."MaLopHP" AS "MaLopHP",
    lhp."TenLopHP" AS "TenLopHP",
    lhp."MaCoSo" AS "CoSoMoLop",
    dk."MaHP" AS "MaHP",
    hp."TenHP" AS "TenHocPhan",
    dk."MaHocKy" AS "MaHocKy",
    dk."NgayDangKy" AS "NgayDangKy"
FROM vw_dangky_toantruong dk
JOIN vw_sinhvien_toantruong sv
    ON sv."MaSV" = dk."MaSV"
JOIN vw_lophocphan_toantruong lhp
    ON lhp."MaLopHP" = dk."MaLopHP"
JOIN "HocPhan" hp
    ON hp."MaHP" = dk."MaHP"
CROSS JOIN params p
WHERE dk."TrangThaiDangKy" = 'DaDangKy'
  AND (p.ma_hk IS NULL OR dk."MaHocKy" = p.ma_hk)
  AND sv."MaCoSo" <> lhp."MaCoSo"
ORDER BY sv."MaSV", dk."NgayDangKy" DESC, dk."MaLopHP";


-- 4. Ty le lap day cua cac lop hoc phan tren toan he thong
WITH params AS (
    SELECT NULL::text AS ma_hk
)
SELECT
    lhp."MaLopHP" AS "MaLopHP",
    lhp."TenLopHP" AS "TenLopHP",
    lhp."MaHP" AS "MaHP",
    hp."TenHP" AS "TenHocPhan",
    lhp."MaHocKy" AS "MaHocKy",
    lhp."MaCoSo" AS "MaCoSo",
    lhp."SiSoHienTai" AS "SiSoHienTai",
    lhp."SiSoToiDa" AS "SiSoToiDa",
    ROUND((lhp."SiSoHienTai"::numeric / NULLIF(lhp."SiSoToiDa", 0)) * 100, 2) AS "TyLeLapDay"
FROM vw_lophocphan_toantruong lhp
JOIN "HocPhan" hp
    ON hp."MaHP" = lhp."MaHP"
CROSS JOIN params p
WHERE lhp."TrangThaiLop" = 'Mo'
  AND (p.ma_hk IS NULL OR lhp."MaHocKy" = p.ma_hk)
ORDER BY "TyLeLapDay" DESC, lhp."MaLopHP";


-- 5a. Thong ke so lop mo theo co so
WITH params AS (
    SELECT NULL::text AS ma_hk
)
SELECT
    lhp."MaCoSo" AS "GroupKey",
    cs."TenCoSo" AS "GroupName",
    COUNT(*) AS "SoLopMo"
FROM vw_lophocphan_toantruong lhp
LEFT JOIN "CoSo" cs
    ON cs."MaCoSo" = lhp."MaCoSo"
CROSS JOIN params p
WHERE lhp."TrangThaiLop" = 'Mo'
  AND (p.ma_hk IS NULL OR lhp."MaHocKy" = p.ma_hk)
GROUP BY lhp."MaCoSo", cs."TenCoSo"
ORDER BY lhp."MaCoSo";


-- 5b. Thong ke so lop mo theo khoa
WITH params AS (
    SELECT NULL::text AS ma_hk
)
SELECT
    hp."MaKhoa" AS "GroupKey",
    k."TenKhoa" AS "GroupName",
    COUNT(*) AS "SoLopMo"
FROM vw_lophocphan_toantruong lhp
JOIN "HocPhan" hp
    ON hp."MaHP" = lhp."MaHP"
LEFT JOIN "Khoa" k
    ON k."MaKhoa" = hp."MaKhoa"
CROSS JOIN params p
WHERE lhp."TrangThaiLop" = 'Mo'
  AND (p.ma_hk IS NULL OR lhp."MaHocKy" = p.ma_hk)
GROUP BY hp."MaKhoa", k."TenKhoa"
ORDER BY hp."MaKhoa";
