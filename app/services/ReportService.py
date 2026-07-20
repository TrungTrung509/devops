from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import text

from configs.db import open_db_by_branch
from enums.status import ClassSectionStatus, EnrollmentStatus
from models.CourseSections import CourseSection
from models.Enrollments import Enrollment
from schemas.Report import (
    BranchRegistrationStat,
    BranchRegistrationStatsResponse,
    CrossBranchEnrollmentStat,
    CrossBranchEnrollmentStatsResponse,
    OpenSectionStat,
    OpenSectionStatsResponse,
    ReportSummaryResponse,
    SectionOccupancyStat,
    SectionOccupancyStatsResponse,
    SectionSummary,
    TopCourseStat,
    TopCourseStatsResponse,
)


class ReportService:
    DISTRIBUTED_SOURCE_SITE = "HADONG"

    @staticmethod
    def _normalize_source_site(source_site: Optional[str]) -> str:
        site = (source_site or ReportService.DISTRIBUTED_SOURCE_SITE).upper()
        if site not in {"HADONG", "HOALAC", "NGOCTRUC"}:
            raise HTTPException(status_code=400, detail=f"sourceSite khong hop le: {site}")
        return site

    @staticmethod
    def _run_distributed_query(
        sql: str,
        *,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, List[Dict]]:
        site = ReportService._normalize_source_site(source_site)
        params: Dict[str, str | None] = {
            "ma_hk": ma_hk,
            "enrollment_status": EnrollmentStatus.DaDangKy.value,
            "section_status": ClassSectionStatus.Mo.value,
        }
        if extra_params:
            params.update(extra_params)

        with open_db_by_branch(site) as db:
            rows = db.execute(text(sql), params).mappings().all()
            return site, [dict(row) for row in rows]

    @staticmethod
    def get_site_summary(site: str, ma_hk: str = None) -> ReportSummaryResponse:
        with open_db_by_branch(site) as db:
            enroll_query = db.query(Enrollment).filter(
                Enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy
            )
            if ma_hk:
                enroll_query = enroll_query.filter(Enrollment.MaHocKy == ma_hk)

            total_registrations = enroll_query.count()
            total_students = enroll_query.distinct(Enrollment.userId).count()

            section_query = db.query(CourseSection).filter(
                CourseSection.TrangThaiLop == ClassSectionStatus.Mo
            )
            if ma_hk:
                section_query = section_query.filter(CourseSection.MaHocKy == ma_hk)

            sections_data = section_query.all()
            total_sections = len(sections_data)
            total_capacity = sum(section.SiSoToiDa for section in sections_data)
            total_enrolled = sum(section.SiSoHienTai for section in sections_data)

            sections_summary = []
            full_count = 0
            for section in sections_data:
                is_full = section.SiSoHienTai >= section.SiSoToiDa
                if is_full:
                    full_count += 1

                sections_summary.append(
                    SectionSummary(
                        MaLopHP=section.MaLopHP,
                        TenLopHP=section.TenLopHP,
                        MaHP=section.MaHP,
                        SiSoHienTai=section.SiSoHienTai,
                        SiSoToiDa=section.SiSoToiDa,
                        IsFull=is_full,
                    )
                )

            occupancy_rate = round((total_enrolled / total_capacity * 100), 2) if total_capacity > 0 else 0

            return ReportSummaryResponse(
                MaCoSo=site,
                MaHocKy=ma_hk,
                TotalStudents=total_students,
                TotalRegistrations=total_registrations,
                TotalSections=total_sections,
                TotalCapacity=total_capacity,
                TotalEnrolledSlots=total_enrolled,
                OccupancyRate=occupancy_rate,
                FullSectionsCount=full_count,
                Sections=sections_summary,
            )

    @staticmethod
    def get_global_summary(ma_hk: str = None) -> ReportSummaryResponse:
        sites = ["HADONG", "HOALAC", "NGOCTRUC"]

        global_students = set()
        total_regs = 0
        total_secs = 0
        total_cap = 0
        total_enrolled = 0
        full_count = 0
        all_sections = []

        for site in sites:
            try:
                site_report = ReportService.get_site_summary(site, ma_hk)

                with open_db_by_branch(site) as db:
                    query = db.query(Enrollment.userId).filter(
                        Enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy
                    )
                    if ma_hk:
                        query = query.filter(Enrollment.MaHocKy == ma_hk)
                    global_students.update(row[0] for row in query.all())

                total_regs += site_report.TotalRegistrations
                total_secs += site_report.TotalSections
                total_cap += site_report.TotalCapacity
                total_enrolled += site_report.TotalEnrolledSlots
                full_count += site_report.FullSectionsCount
                all_sections.extend(site_report.Sections)
            except Exception as exc:
                print(f"Error fetching report from {site}: {exc}")

        occupancy_rate = round((total_enrolled / total_cap * 100), 2) if total_cap > 0 else 0

        return ReportSummaryResponse(
            MaCoSo="GLOBAL",
            MaHocKy=ma_hk,
            TotalStudents=len(global_students),
            TotalRegistrations=total_regs,
            TotalSections=total_secs,
            TotalCapacity=total_cap,
            TotalEnrolledSlots=total_enrolled,
            OccupancyRate=occupancy_rate,
            FullSectionsCount=full_count,
            Sections=all_sections,
        )

    @staticmethod
    def get_branch_registration_stats(
        *,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
    ) -> BranchRegistrationStatsResponse:
        sql = """
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
        WHERE dk."TrangThaiDangKy" = :enrollment_status
          AND (:ma_hk IS NULL OR dk."MaHocKy" = :ma_hk)
        GROUP BY sv."MaCoSo", cs."TenCoSo"
        ORDER BY sv."MaCoSo"
        """
        site, rows = ReportService._run_distributed_query(sql, ma_hk=ma_hk, source_site=source_site)
        return BranchRegistrationStatsResponse(
            SourceSite=site,
            MaHocKy=ma_hk,
            Items=[BranchRegistrationStat(**row) for row in rows],
        )

    @staticmethod
    def get_top_course_stats(
        *,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
    ) -> TopCourseStatsResponse:
        sql = """
        WITH ranked_courses AS (
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
            WHERE dk."TrangThaiDangKy" = :enrollment_status
              AND (:ma_hk IS NULL OR dk."MaHocKy" = :ma_hk)
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
        ORDER BY "MaHP"
        """
        site, rows = ReportService._run_distributed_query(sql, ma_hk=ma_hk, source_site=source_site)
        return TopCourseStatsResponse(
            SourceSite=site,
            MaHocKy=ma_hk,
            Items=[TopCourseStat(**row) for row in rows],
        )

    @staticmethod
    def get_cross_branch_enrollment_stats(
        *,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
    ) -> CrossBranchEnrollmentStatsResponse:
        sql = """
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
            dk."NgayDangKy"::text AS "NgayDangKy"
        FROM vw_dangky_toantruong dk
        JOIN vw_sinhvien_toantruong sv
            ON sv."MaSV" = dk."MaSV"
        JOIN vw_lophocphan_toantruong lhp
            ON lhp."MaLopHP" = dk."MaLopHP"
        JOIN "HocPhan" hp
            ON hp."MaHP" = dk."MaHP"
        WHERE dk."TrangThaiDangKy" = :enrollment_status
          AND (:ma_hk IS NULL OR dk."MaHocKy" = :ma_hk)
          AND sv."MaCoSo" <> lhp."MaCoSo"
        ORDER BY sv."MaSV", dk."NgayDangKy" DESC, dk."MaLopHP"
        """
        site, rows = ReportService._run_distributed_query(sql, ma_hk=ma_hk, source_site=source_site)
        return CrossBranchEnrollmentStatsResponse(
            SourceSite=site,
            MaHocKy=ma_hk,
            Items=[CrossBranchEnrollmentStat(**row) for row in rows],
        )

    @staticmethod
    def get_section_occupancy_stats(
        *,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
    ) -> SectionOccupancyStatsResponse:
        sql = """
        SELECT
            lhp."MaLopHP" AS "MaLopHP",
            lhp."TenLopHP" AS "TenLopHP",
            lhp."MaHP" AS "MaHP",
            hp."TenHP" AS "TenHocPhan",
            lhp."MaHocKy" AS "MaHocKy",
            lhp."MaCoSo" AS "MaCoSo",
            lhp."SiSoHienTai" AS "SiSoHienTai",
            lhp."SiSoToiDa" AS "SiSoToiDa",
            ROUND((lhp."SiSoHienTai"::numeric / NULLIF(lhp."SiSoToiDa", 0)) * 100, 2)::float AS "TyLeLapDay"
        FROM vw_lophocphan_toantruong lhp
        JOIN "HocPhan" hp
            ON hp."MaHP" = lhp."MaHP"
        WHERE lhp."TrangThaiLop" = :section_status
          AND (:ma_hk IS NULL OR lhp."MaHocKy" = :ma_hk)
        ORDER BY "TyLeLapDay" DESC, lhp."MaLopHP"
        """
        site, rows = ReportService._run_distributed_query(sql, ma_hk=ma_hk, source_site=source_site)
        return SectionOccupancyStatsResponse(
            SourceSite=site,
            MaHocKy=ma_hk,
            Items=[SectionOccupancyStat(**row) for row in rows],
        )

    @staticmethod
    def get_open_section_stats(
        *,
        group_by: str,
        ma_hk: Optional[str] = None,
        source_site: Optional[str] = None,
    ) -> OpenSectionStatsResponse:
        normalized_group_by = (group_by or "").lower()
        if normalized_group_by not in {"branch", "department"}:
            raise HTTPException(status_code=400, detail="groupBy phai la 'branch' hoac 'department'")

        if normalized_group_by == "branch":
            sql = """
            SELECT
                lhp."MaCoSo" AS "GroupKey",
                cs."TenCoSo" AS "GroupName",
                COUNT(*) AS "SoLopMo"
            FROM vw_lophocphan_toantruong lhp
            LEFT JOIN "CoSo" cs
                ON cs."MaCoSo" = lhp."MaCoSo"
            WHERE lhp."TrangThaiLop" = :section_status
              AND (:ma_hk IS NULL OR lhp."MaHocKy" = :ma_hk)
            GROUP BY lhp."MaCoSo", cs."TenCoSo"
            ORDER BY lhp."MaCoSo"
            """
        else:
            sql = """
            SELECT
                hp."MaKhoa" AS "GroupKey",
                k."TenKhoa" AS "GroupName",
                COUNT(*) AS "SoLopMo"
            FROM vw_lophocphan_toantruong lhp
            JOIN "HocPhan" hp
                ON hp."MaHP" = lhp."MaHP"
            LEFT JOIN "Khoa" k
                ON k."MaKhoa" = hp."MaKhoa"
            WHERE lhp."TrangThaiLop" = :section_status
              AND (:ma_hk IS NULL OR lhp."MaHocKy" = :ma_hk)
            GROUP BY hp."MaKhoa", k."TenKhoa"
            ORDER BY hp."MaKhoa"
            """

        site, rows = ReportService._run_distributed_query(sql, ma_hk=ma_hk, source_site=source_site)
        return OpenSectionStatsResponse(
            SourceSite=site,
            MaHocKy=ma_hk,
            GroupBy=normalized_group_by,
            Items=[OpenSectionStat(**row) for row in rows],
        )
