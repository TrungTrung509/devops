from enum import Enum

class UserRole(str, Enum):
    SinhVien = "SinhVien"
    GiangVien = "GiangVien"
    Admin = "Admin"
