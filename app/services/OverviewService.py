from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text

from configs.db import open_db_by_branch
from schemas.Overview import (
    AdminOverviewResponse,
    ExtraStat,
    SiteStat,
    StatusStat,
)

SITES_CONFIG: Dict[str, str] = {
    "HADONG": "Hà Đông",
    "NGOCTRUC": "Ngọc Trực",
    "HOALAC": "Hòa Lạc",
}
SITE_KEYS = list(SITES_CONFIG.keys())
SITE_NAMES = SITES_CONFIG


def _build_site_stats(rows: List[Dict], total: int) -> List[SiteStat]:
    stats = []
    for site, name in SITE_NAMES.items():
        count = 0
        for row in rows:
            row_site = row.get("site") or row.get("MaCoSo") or row.get("ma_co_so") or ""
            if row_site == site:
                count = row.get("count", 0)
                break
        pct = round(count / total * 100, 2) if total > 0 else 0.0
        stats.append(SiteStat(site=site, site_name=name, count=count, percentage=pct))
    return stats


class OverviewService:
    DISTRIBUTED_SOURCE_SITE = "HADONG"

    @staticmethod
    def _normalize_entity(entity: str) -> str:
        e = entity.lower().strip()
        valid = {"teachers", "students", "courses", "semesters", "classrooms", "class-sections"}
        if e not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Entity khong hop le. Dung: {', '.join(sorted(valid))}",
            )
        return e

    @staticmethod
    def _run_distributed_query(sql: str, source_site: str = "HADONG") -> List[Dict]:
        with open_db_by_branch(source_site) as db:
            rows = db.execute(text(sql)).mappings().all()
            return [dict(row) for row in rows]

    @staticmethod
    def _run_site_query(sql: str, site: str) -> List[Dict]:
        with open_db_by_branch(site) as db:
            rows = db.execute(text(sql)).mappings().all()
            return [dict(row) for row in rows]

    # ─── STUDENTS ────────────────────────────────────────────────────────────────

    @classmethod
    def get_students_overview(cls) -> AdminOverviewResponse:
        # Total from distributed view
        total_sql = """
        SELECT COUNT(*)::int AS total FROM vw_sinhvien_toantruong
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        # By site from distributed view
        by_site_sql = """
        SELECT "MaCoSo" AS site, COUNT(*)::int AS count
        FROM vw_sinhvien_toantruong
        GROUP BY "MaCoSo"
        ORDER BY "MaCoSo"
        """
        rows_site = cls._run_distributed_query(by_site_sql)
        by_site = _build_site_stats(rows_site, total)

        # By status from distributed view
        by_status_sql = """
        SELECT "TrangThai" AS status, COUNT(*)::int AS count
        FROM vw_sinhvien_toantruong
        GROUP BY "TrangThai"
        ORDER BY "TrangThai"
        """
        rows_status = cls._run_distributed_query(by_status_sql)
        status_map = {
            "DangHoc": "Đang học",
            "BaoLuu": "Bảo lưu",
            "ThoiHoc": "Thôi học",
            "TotNghiep": "Tốt nghiệp",
        }
        by_status = [
            StatusStat(status=r["status"], label=status_map.get(r["status"], r["status"]), count=r["count"])
            for r in rows_status
        ]

        return AdminOverviewResponse(
            entity="students",
            title="Sinh viên",
            description="Thống kê tổng quan toàn trường về số lượng sinh viên theo cơ sở và trạng thái học tập.",
            total=total,
            by_site=by_site,
            by_status=by_status,
            extra=[],
        )

    # ─── TEACHERS ───────────────────────────────────────────────────────────────

    @classmethod
    def get_teachers_overview(cls) -> AdminOverviewResponse:
        total_sql = """
        SELECT COUNT(*)::int AS total FROM vw_giangvien_toantruong
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        by_site_sql = """
        SELECT "MaCoSo" AS site, COUNT(*)::int AS count
        FROM vw_giangvien_toantruong
        GROUP BY "MaCoSo"
        ORDER BY "MaCoSo"
        """
        rows_site = cls._run_distributed_query(by_site_sql)
        by_site = _build_site_stats(rows_site, total)

        by_status_sql = """
        SELECT "TrangThai" AS status, COUNT(*)::int AS count
        FROM vw_giangvien_toantruong
        GROUP BY "TrangThai"
        ORDER BY "TrangThai"
        """
        rows_status = cls._run_distributed_query(by_status_sql)
        status_map = {
            "DangCongTac": "Đang công tác",
            "TamNghi": "Tạm nghỉ",
            "NghiViec": "Đã nghỉ",
        }
        by_status = [
            StatusStat(status=r["status"], label=status_map.get(r["status"], r["status"]), count=r["count"])
            for r in rows_status
        ]

        return AdminOverviewResponse(
            entity="teachers",
            title="Giảng viên",
            description="Thống kê tổng quan toàn trường về số lượng giảng viên theo cơ sở và trạng thái công tác.",
            total=total,
            by_site=by_site,
            by_status=by_status,
            extra=[],
        )

    # ─── COURSES ───────────────────────────────────────────────────────────────

    @classmethod
    def get_courses_overview(cls) -> AdminOverviewResponse:
        # HocPhan is replicated/common - query from primary site only to avoid duplicates
        total_sql = """
        SELECT COUNT(*)::int AS total FROM "HocPhan"
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        by_type_sql = """
        SELECT "LoaiHocPhan" AS status, COUNT(*)::int AS count
        FROM "HocPhan"
        GROUP BY "LoaiHocPhan"
        ORDER BY "LoaiHocPhan"
        """
        rows_type = cls._run_distributed_query(by_type_sql)
        type_map = {
            "BatBuoc": "Bắt buộc",
            "TuChon": "Tự chọn",
            "BatBuocCoSo": "Bắt buộc cơ sở",
        }
        by_status = [
            StatusStat(status=r["status"], label=type_map.get(r["status"], r["status"] or "Khác"), count=r["count"])
            for r in rows_type
        ]

        by_khoa_sql = """
        SELECT k."MaKhoa" AS site, k."TenKhoa" AS site_name, COUNT(*)::int AS count
        FROM "HocPhan" hp
        LEFT JOIN "Khoa" k ON k."MaKhoa" = hp."MaKhoa"
        GROUP BY k."MaKhoa", k."TenKhoa"
        ORDER BY count DESC
        LIMIT 20
        """
        rows_khoa = cls._run_distributed_query(by_khoa_sql)
        extra = [
            ExtraStat(
                key=r.get("site") or "",
                label=r.get("site_name") or r.get("site") or "—",
                count=r.get("count", 0),
                percentage=round(r.get("count", 0) / total * 100, 2) if total > 0 else 0.0,
            )
            for r in rows_khoa
        ]

        return AdminOverviewResponse(
            entity="courses",
            title="Học phần",
            description="Thống kê học phần dùng chung toàn trường. Dữ liệu được quản lý tập trung tại cơ sở chính.",
            total=total,
            by_site=[
                SiteStat(site="COMMON", site_name="Dữ liệu dùng chung toàn trường", count=total, percentage=100.0)
            ],
            by_status=by_status,
            extra=extra,
        )

    # ─── SEMESTERS ───────────────────────────────────────────────────────────────

    @classmethod
    def get_semesters_overview(cls) -> AdminOverviewResponse:
        total_sql = """
        SELECT COUNT(*)::int AS total FROM "HocKy"
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        by_status_sql = """
        SELECT "TrangThaiHocKy" AS status, COUNT(*)::int AS count
        FROM "HocKy"
        GROUP BY "TrangThaiHocKy"
        ORDER BY "TrangThaiHocKy"
        """
        rows_status = cls._run_distributed_query(by_status_sql)
        status_map = {
            "SapMo": "Sắp mở",
            "DangDangKy": "Đang đăng ký",
            "DangHoc": "Đang học",
            "DaKetThuc": "Đã kết thúc",
        }
        by_status = [
            StatusStat(status=r["status"], label=status_map.get(r["status"], r["status"] or "—"), count=r["count"])
            for r in rows_status
        ]

        by_year_sql = """
        SELECT "NamHoc" AS site, COUNT(*)::int AS count
        FROM "HocKy"
        WHERE "NamHoc" IS NOT NULL
        GROUP BY "NamHoc"
        ORDER BY "NamHoc" DESC
        LIMIT 10
        """
        rows_year = cls._run_distributed_query(by_year_sql)
        extra = [
            ExtraStat(key=r.get("site") or "", label=r.get("site") or "—", count=r.get("count", 0))
            for r in rows_year
        ]

        return AdminOverviewResponse(
            entity="semesters",
            title="Học kỳ",
            description="Thống kê học kỳ dùng chung toàn trường. Dữ liệu được quản lý tập trung tại cơ sở chính.",
            total=total,
            by_site=[
                SiteStat(site="COMMON", site_name="Dữ liệu dùng chung toàn trường", count=total, percentage=100.0)
            ],
            by_status=by_status,
            extra=extra,
        )

    # ─── CLASSROOMS ─────────────────────────────────────────────────────────────

    @classmethod
    def get_classrooms_overview(cls) -> AdminOverviewResponse:
        total_sql = """
        SELECT COUNT(*)::int AS total FROM vw_phonghoc_toantruong
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        by_site_sql = """
        SELECT "MaCoSo" AS site, COUNT(*)::int AS count
        FROM vw_phonghoc_toantruong
        GROUP BY "MaCoSo"
        ORDER BY "MaCoSo"
        """
        rows_site = cls._run_distributed_query(by_site_sql)
        by_site = _build_site_stats(rows_site, total)

        by_type_sql = """
        SELECT "LoaiPhong" AS status, COUNT(*)::int AS count
        FROM vw_phonghoc_toantruong
        WHERE "LoaiPhong" IS NOT NULL
        GROUP BY "LoaiPhong"
        ORDER BY count DESC
        """
        rows_type = cls._run_distributed_query(by_type_sql)
        type_map = {
            "LyThuyet": "Lý thuyết",
            "ThucHanh": "Thực hành",
            "MayTinh": "Phòng máy",
            "HoiTruong": "Hội trường",
            "ThiNghiem": "Thí nghiệm",
            "PhongMay": "Phòng máy",
            "Khac": "Khác",
        }
        by_status = [
            StatusStat(status=r["status"], label=type_map.get(r["status"], r["status"] or "Khác"), count=r["count"])
            for r in rows_type
        ]

        by_active_sql = """
        SELECT "TrangThai" AS status, COUNT(*)::int AS count
        FROM vw_phonghoc_toantruong
        WHERE "TrangThai" IS NOT NULL
        GROUP BY "TrangThai"
        ORDER BY "TrangThai"
        """
        rows_active = cls._run_distributed_query(by_active_sql)
        active_map = {
            "HoatDong": "Hoạt động",
            "BaoTri": "Bảo trì",
            "NgungSuDung": "Ngừng sử dụng",
        }
        extra = [
            ExtraStat(
                key=r["status"],
                label=active_map.get(r["status"], r["status"] or "—"),
                count=r["count"],
                percentage=round(r["count"] / total * 100, 2) if total > 0 else 0.0,
            )
            for r in rows_active
        ]

        return AdminOverviewResponse(
            entity="classrooms",
            title="Phòng học",
            description="Thống kê tổng quan toàn trường về số lượng phòng học theo cơ sở, loại phòng và trạng thái hoạt động.",
            total=total,
            by_site=by_site,
            by_status=by_status,
            extra=extra,
        )

    # ─── CLASS SECTIONS ─────────────────────────────────────────────────────────

    @classmethod
    def get_class_sections_overview(cls) -> AdminOverviewResponse:
        total_sql = """
        SELECT COUNT(*)::int AS total FROM vw_lophocphan_toantruong
        """
        rows_total = cls._run_distributed_query(total_sql)
        total = rows_total[0]["total"] if rows_total else 0

        by_site_sql = """
        SELECT "MaCoSo" AS site, COUNT(*)::int AS count
        FROM vw_lophocphan_toantruong
        GROUP BY "MaCoSo"
        ORDER BY "MaCoSo"
        """
        rows_site = cls._run_distributed_query(by_site_sql)
        by_site = _build_site_stats(rows_site, total)

        by_status_sql = """
        SELECT "TrangThaiLop" AS status, COUNT(*)::int AS count
        FROM vw_lophocphan_toantruong
        GROUP BY "TrangThaiLop"
        ORDER BY "TrangThaiLop"
        """
        rows_status = cls._run_distributed_query(by_status_sql)
        status_map = {
            "Mo": "Mở",
            "Dong": "Đóng",
            "Huy": "Hủy",
        }
        by_status = [
            StatusStat(status=r["status"], label=status_map.get(r["status"], r["status"] or "—"), count=r["count"])
            for r in rows_status
        ]

        # Average fill rate
        avg_fill_sql = """
        SELECT
            ROUND(
                AVG("SiSoHienTai"::numeric / NULLIF("SiSoToiDa", 0) * 100), 2
            )::float AS avg_fill_rate,
            SUM("SiSoHienTai")::int AS total_enrolled,
            SUM("SiSoToiDa")::int AS total_capacity
        FROM vw_lophocphan_toantruong
        WHERE "SiSoToiDa" > 0
        """
        rows_avg = cls._run_distributed_query(avg_fill_sql)
        extra = []
        if rows_avg and rows_avg[0].get("avg_fill_rate") is not None:
            r = rows_avg[0]
            extra.append(
                ExtraStat(
                    key="avg_fill_rate",
                    label="Tỷ lệ lấp đầy trung bình",
                    count=int(r["avg_fill_rate"] or 0),
                    percentage=None,
                )
            )
            extra.append(
                ExtraStat(key="total_enrolled", label="Tổng SV đăng ký", count=int(r["total_enrolled"] or 0))
            )
            extra.append(
                ExtraStat(key="total_capacity", label="Tổng sức chứa", count=int(r["total_capacity"] or 0))
            )

        return AdminOverviewResponse(
            entity="class-sections",
            title="Lớp học phần",
            description="Thống kê tổng quan toàn trường về số lượng lớp học phần theo cơ sở, trạng thái và tỷ lệ lấp đầy.",
            total=total,
            by_site=by_site,
            by_status=by_status,
            extra=extra,
        )

    # ─── DISPATCHER ─────────────────────────────────────────────────────────────

    @classmethod
    def get_overview(cls, entity: str) -> AdminOverviewResponse:
        e = cls._normalize_entity(entity)
        if e == "students":
            return cls.get_students_overview()
        if e == "teachers":
            return cls.get_teachers_overview()
        if e == "courses":
            return cls.get_courses_overview()
        if e == "semesters":
            return cls.get_semesters_overview()
        if e == "classrooms":
            return cls.get_classrooms_overview()
        if e == "class-sections":
            return cls.get_class_sections_overview()
        # Should not reach here due to _normalize_entity
        raise HTTPException(status_code=400, detail="Entity không hợp lệ")
