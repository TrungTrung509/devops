import sys
import os
import random
sys.path.insert(0, os.path.dirname(__file__))

from configs.db import engines, Base
from models.models import User, SinhVien, CourseSection
from sqlalchemy.orm import Session

# 3 môn học cố định - mỗi môn được xếp vào 1 ngày riêng để không trùng lịch nhau
COURSES = [
    {"MaHP": "IT01", "Thu": 2, "Tiets": [1, 3, 5, 7]},   # Thứ 2
    {"MaHP": "IT02", "Thu": 4, "Tiets": [1, 3, 5, 7]},   # Thứ 4
    {"MaHP": "IT03", "Thu": 6, "Tiets": [1, 3, 5, 7]},   # Thứ 6
]
CLASSES_PER_COURSE = 100  # 100 lớp/môn/site → Tổng 300 lớp/site, 900 lớp cả 3 site

def seed_database():
    sites = ["HD", "HL", "NT"]

    # Chuẩn bị toàn bộ 12.000 users trước (để nhân bản cho cả 3 site)
    all_users = []
    for site in sites:
        for i in range(1, 4001):
            uid = f"SV{site}{i:04d}"
            all_users.append(User(userId=uid, role="SinhVien"))

    for site in sites:
        print(f"[{site}] Đang khởi tạo Schema...")
        engine = engines[site]
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        with Session(engine) as db:
            print(f"[{site}] Bơm dữ liệu...")

            # 1. Bơm tất cả 12.000 users vào bảng nhân bản cục bộ
            db.bulk_save_objects(all_users)

            # 2. Bơm 4.000 sinh viên thuộc site này
            students = []
            for i in range(1, 4001):
                uid = f"SV{site}{i:04d}"
                students.append(SinhVien(MaSV=uid, userId=uid, MaCoSo=site))
            db.bulk_save_objects(students)

            # Lớp học phần: 3 môn × 60 lớp mỗi môn
            classes = []
            lop_idx = 1
            for course in COURSES:
                for j in range(CLASSES_PER_COURSE):
                    tiet_start = course["Tiets"][j % len(course["Tiets"])]
                    classes.append(CourseSection(
                        MaLopHP=f"{site}_{course['MaHP']}_{lop_idx:03d}",
                        MaHP=course["MaHP"],
                        MaHocKy="HK1_2026",
                        SiSoToiDa=80,
                        SiSoHienTai=0,
                        ThuTrongTuan=course["Thu"],
                        TietBatDau=tiet_start,
                        SoTiet=2,
                    ))
                    lop_idx += 1

            db.bulk_save_objects(classes)
            db.commit()
            print(f"[{site}] ✓ 4.000 SV | 300 lớp (3 môn × 100 lớp)")

if __name__ == "__main__":
    seed_database()
    print("\n✅ HOÀN THÀNH SEED DATA COSO! (12.000 SV tổng | 900 lớp tổng | 3 môn cố định)")
