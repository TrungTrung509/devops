from enum import Enum

class RoomType(str, Enum):
    LyThuyet = "LyThuyet"
    ThucHanh = "ThucHanh"
    PhongMay = "PhongMay"
    MayTinh = "MayTinh"
    HoiTruong = "HoiTruong"
    ThiNghiem = "ThiNghiem"
    Khac = "Khac"

class CourseType(str, Enum):
    BatBuoc = "BatBuoc"
    TuChon = "TuChon"

class StudyForm(str, Enum):
    Offline = "Offline"
    Online = "Online"
    Hybrid = "Hybrid"
