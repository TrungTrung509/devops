from typing import List, Optional

from pydantic import BaseModel


class SectionSummary(BaseModel):
    MaLopHP: str
    TenLopHP: Optional[str]
    MaHP: str
    SiSoHienTai: int
    SiSoToiDa: int
    IsFull: bool


class ReportSummaryResponse(BaseModel):
    MaCoSo: Optional[str] = "GLOBAL"
    MaHocKy: Optional[str]
    TotalStudents: int
    TotalRegistrations: int
    TotalSections: int
    TotalCapacity: int
    TotalEnrolledSlots: int
    OccupancyRate: float
    FullSectionsCount: int
    Sections: List[SectionSummary] = []


class BranchRegistrationStat(BaseModel):
    MaCoSo: str
    TenCoSo: Optional[str]
    SoSinhVienDangKy: int
    SoLuotDangKy: int


class BranchRegistrationStatsResponse(BaseModel):
    SourceSite: str
    MaHocKy: Optional[str]
    Items: List[BranchRegistrationStat]


class TopCourseStat(BaseModel):
    MaHP: str
    TenHocPhan: str
    MaKhoa: str
    SoSinhVienDangKy: int
    SoLuotDangKy: int


class TopCourseStatsResponse(BaseModel):
    SourceSite: str
    MaHocKy: Optional[str]
    Items: List[TopCourseStat]


class CrossBranchEnrollmentStat(BaseModel):
    MaSV: str
    HoTen: str
    CoSoSinhVien: str
    MaLopHP: str
    TenLopHP: Optional[str]
    CoSoMoLop: str
    MaHP: str
    TenHocPhan: str
    MaHocKy: str
    NgayDangKy: str


class CrossBranchEnrollmentStatsResponse(BaseModel):
    SourceSite: str
    MaHocKy: Optional[str]
    Items: List[CrossBranchEnrollmentStat]


class SectionOccupancyStat(BaseModel):
    MaLopHP: str
    TenLopHP: Optional[str]
    MaHP: str
    TenHocPhan: str
    MaHocKy: str
    MaCoSo: str
    SiSoHienTai: int
    SiSoToiDa: int
    TyLeLapDay: float


class SectionOccupancyStatsResponse(BaseModel):
    SourceSite: str
    MaHocKy: Optional[str]
    Items: List[SectionOccupancyStat]


class OpenSectionStat(BaseModel):
    GroupKey: str
    GroupName: Optional[str]
    SoLopMo: int


class OpenSectionStatsResponse(BaseModel):
    SourceSite: str
    MaHocKy: Optional[str]
    GroupBy: str
    Items: List[OpenSectionStat]
