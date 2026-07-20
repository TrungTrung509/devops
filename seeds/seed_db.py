import sys
import os
from datetime import datetime, date
import bcrypt

# Monkeypatch bcrypt to fix passlib compatibility with python 3.12+ / bcrypt 4.0.0+
original_hashpw = bcrypt.hashpw
def safe_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    elif isinstance(password, str) and len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72]
    return original_hashpw(password, salt)
bcrypt.hashpw = safe_hashpw

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

# Tự động nạp các biến môi trường khi chạy local ngoài Docker
from dotenv import load_dotenv
app_env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
app_example_env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.example.env')
if os.path.exists(app_env_path):
    load_dotenv(app_env_path)
elif os.path.exists(app_example_env_path):
    load_dotenv(app_example_env_path)

from configs.db import engines
from configs.config import pwd_context
from sqlalchemy import text

NUM_STUDENTS = 700
NUM_TEACHERS = 40
NUM_ROOMS = 15
SECTIONS_PER_COURSE = 15

YEAR_PREFIX = str(datetime.now().year)[2:]
DEPT_CODE = "CNTT"

BRANCHES = {
    "HADONG": {
        "code": "HD",
        "address": "Ha Dong, Ha Noi",
        "domain": "hadong.ptit.edu.vn"
    },
    "HOALAC": {
        "code": "HL",
        "address": "Hoa Lac, Ha Noi",
        "domain": "hoalac.ptit.edu.vn"
    },
    "NGOCTRUC": {
        "code": "NT",
        "address": "Ngoc Truc, Ha Noi",
        "domain": "ngoctruc.ptit.edu.vn"
    }
}

# 1. Generate user, student, and teacher datasets
users_data = []    
students_data = {}   
teachers_data = {}  

for site in BRANCHES.keys():
    students_data[site] = []
    teachers_data[site] = []

print("Generating datasets and hashing passwords (password = 123456)...")
DEFAULT_PASSWORD_HASH = pwd_context.hash("123456")

# Generate Students
for site, info in BRANCHES.items():
    for i in range(1, NUM_STUDENTS + 1):
        num_str = f"{i:03d}"  # 3 digits STT (001, 002, ...)
        ma_sv = f"SV{info['code']}{YEAR_PREFIX}{DEPT_CODE}{num_str}"
        
        # User details
        user_detail = {
            "user_id": ma_sv,
            "username": ma_sv,
            "password": DEFAULT_PASSWORD_HASH,
            "email": f"{ma_sv}@{info['domain']}",
            "role": "SinhVien",
            "branch": site,
            "status": "Active",
            "created_at": datetime.utcnow().isoformat()
        }
        users_data.append(user_detail)

        # Student details
        student_detail = {
            "ma_sv": ma_sv,
            "user_id": ma_sv,
            "ho": "Nguyen",
            "ten": f"Sinh Vien {i:02d}",
            "ngay_sinh": date(2004, 1, 15),
            "gioi_tinh": "Nam" if i % 2 == 1 else "Nu",
            "sdt": f"0900000{info['code']}{i:02d}",
            "dia_chi": f"Khu vuc {site.capitalize()}, Ha Noi",
            "ma_coso": site,
            "ma_khoa": DEPT_CODE,
            "trang_thai": "DangHoc",
            "ngay_nhap_hoc": date(2022, 9, 1),
            "ngay_tao": datetime.utcnow().isoformat()
        }
        students_data[site].append(student_detail)

# Generate Teachers
for site, info in BRANCHES.items():
    for i in range(1, NUM_TEACHERS + 1):
        num_str = f"{i:03d}" 
        ma_gv = f"GV{info['code']}{YEAR_PREFIX}{DEPT_CODE}{num_str}"

        # User details
        user_detail = {
            "user_id": ma_gv,
            "username": ma_gv,
            "password": DEFAULT_PASSWORD_HASH, 
            "email": f"{ma_gv}@{info['domain']}",
            "role": "GiangVien",
            "branch": site,
            "status": "Active",
            "created_at": datetime.utcnow().isoformat()
        }
        users_data.append(user_detail)

        # Teacher details
        teacher_detail = {
            "ma_gv": ma_gv,
            "user_id": ma_gv,
            "ho": "Tran" if i % 2 == 1 else "Le",
            "ten": f"Giang Vien {i:02d}",
            "ngay_sinh": date(1980 + i, 5, 20),
            "gioi_tinh": "Nam" if i % 2 == 1 else "Nu",
            "hoc_vi": "TienSi" if i <= 10 else "ThacSi",
            "hoc_ham": "PhoGiaoSu" if i <= 3 else "GiangVien",
            "sdt": f"0901000{info['code']}{i:02d}",
            "dia_chi": info['address'],
            "ma_coso": site,
            "ma_khoa": DEPT_CODE,
            "trang_thai": "DangCongTac",
            "ngay_vao_lam": date(2015, 9, 1),
            "ngay_tao": datetime.utcnow().isoformat()
        }
        teachers_data[site].append(teacher_detail)

# Admin user details
admin_detail = {
    "user_id": "ADMIN1",
    "username": "admin",
    "password": pwd_context.hash("admin123"),
    "email": "admin@system.com",
    "role": "Admin",
    "branch": "HADONG",
    "status": "Active",
    "created_at": datetime.utcnow().isoformat()
}

semester_detail = {
    "ma_hoc_ky": "HK2-2025",
    "nam_hoc": "2025-2026",
    "ky_so": 2,
    "ngay_bd": date(2025, 8, 15),
    "ngay_kt": date(2025, 11, 15),
    "trang_thai": "DangDangKy"
}

# 8 Common Courses to seed on all sites (All BatBuoc)
courses_data = [
    {
        "ma_hp": "GDTC1102",
        "ten_hp": "Giáo dục thể chất 2",
        "so_tc": 2,
        "so_tiet_lt": 0,
        "so_tiet_th": 60,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Giáo dục thể chất 2",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "MLN1102",
        "ten_hp": "Kinh tế chính trị Mác- Lênin",
        "so_tc": 2,
        "so_tiet_lt": 30,
        "so_tiet_th": 0,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Kinh tế chính trị Mác- Lênin",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "ENG1101",
        "ten_hp": "Tiếng Anh (Course 1)",
        "so_tc": 3,
        "so_tiet_lt": 45,
        "so_tiet_th": 0,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Tiếng Anh (Course 1)",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "BAS1204",
        "ten_hp": "Giải tích 2",
        "so_tc": 3,
        "so_tiet_lt": 45,
        "so_tiet_th": 0,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Giải tích 2",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "BAS1224",
        "ten_hp": "Vật lý ứng dụng",
        "so_tc": 3,
        "so_tiet_lt": 30,
        "so_tiet_th": 15,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Vật lý ứng dụng",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "BAS1105",
        "ten_hp": "Pháp luật đại cương",
        "so_tc": 2,
        "so_tiet_lt": 30,
        "so_tiet_th": 0,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Pháp luật đại cương",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "INT1319",
        "ten_hp": "Kỹ thuật số",
        "so_tc": 3,
        "so_tiet_lt": 30,
        "so_tiet_th": 15,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Kỹ thuật số",
        "trang_thai": "HoatDong"
    },
    {
        "ma_hp": "INT1155",
        "ten_hp": "Tin học cơ sở 2",
        "so_tc": 3,
        "so_tiet_lt": 30,
        "so_tiet_th": 15,
        "loai_hp": "BatBuoc",
        "ma_khoa": "CNTT",
        "mo_ta": "Học phần Tin học cơ sở 2",
        "trang_thai": "HoatDong"
    }
]

# Generate Classrooms
classrooms_data = {}
for site, info in BRANCHES.items():
    classrooms_data[site] = []
    for i in range(1, NUM_ROOMS + 1): # 15 rooms
        room_id = f"{info['code']}_{100+i}"
        toa_part = "A1" if i <= 8 else "B1"
        classrooms_data[site].append({
            "ma_phong": room_id,
            "ten_phong": f"{100+i}-{toa_part}-{info['code']}",
            "toa_nha": toa_part,
            "tang": (i - 1) // 5 + 1,
            "suc_chua": 80,
            "loai_phong": "LyThuyet" if i % 2 == 1 else "MayTinh",
            "ma_coso": site,
            "trang_thai": "HoatDong"
        })

# Generate Class Sections and Schedules
sections_data = {}
schedules_data = {}

tiets_pool = [1, 3, 6, 8]

for site, info in BRANCHES.items():
    sections_data[site] = []
    schedules_data[site] = []
    
    for j, c in enumerate(courses_data):
        ma_hp = c["ma_hp"]
        ten_hp = c["ten_hp"]
        
        # Max capacity based on course type
        if ma_hp in ["GDTC1102", "MLN1102", "BAS1105"]:
            si_so_max = 60
        elif ma_hp in ["BAS1204", "BAS1224", "INT1155"]:
            si_so_max = 50
        else:
            si_so_max = 45

        for k in range(1, SECTIONS_PER_COURSE + 1): # 15 class sections: Nhóm 01 to Nhóm 15
            nhom_str = f"{k:02d}"
            ma_lop_hp = f"{site}_{ma_hp}_{nhom_str}"
            
            # Select teacher index (1 to 40) using Round-Robin
            t_idx = ((j * SECTIONS_PER_COURSE + (k - 1)) % NUM_TEACHERS) + 1
            ma_gv = f"GV{info['code']}{YEAR_PREFIX}{DEPT_CODE}{t_idx:03d}"
            
            # Select room index (1 to 15) using Round-Robin
            r_idx = ((j * SECTIONS_PER_COURSE + (k - 1)) % NUM_ROOMS) + 1
            ma_phong = f"{info['code']}_{100+r_idx}"
            
            section_detail = {
                "ma_lop_hp": ma_lop_hp,
                "ma_hp": ma_hp,
                "ma_hoc_ky": "HK2-2025",
                "ma_coso": site,
                "ma_gv": ma_gv,
                "ten_lop_hp": nhom_str,
                "si_so_toi_da": si_so_max,
                "si_so_hien_tai": 0,
                "hinh_thuc_hoc": "Offline",
                "trang_thai_lop": "Mo"
            }
            sections_data[site].append(section_detail)
            
            # Spread days over Monday to Saturday (day 2 to 7)
            day = 2 + (j * 2 + (k - 1)) % 6
            # Spread starting period over the pool [1, 3, 6, 8]
            tiet = tiets_pool[(k - 1) % len(tiets_pool)]
            
            # Alternating periods based on course index j
            if j % 2 == 0:
                so_tiet_s1 = 2
                so_tiet_s2 = 3
            else:
                so_tiet_s1 = 3
                so_tiet_s2 = 2
            
            # Schedule 1: First half (2025-08-15 to 2025-09-30)
            sch1_detail = {
                "ma_lich": f"LH_{info['code']}_{ma_hp}_{nhom_str}_S1",
                "ma_lop_hp": ma_lop_hp,
                "ma_phong": ma_phong,
                "thu_trong_tuan": day,
                "tiet_bat_dau": tiet,
                "so_tiet": so_tiet_s1,
                "ngay_bat_dau": date(2025, 8, 15),
                "ngay_ket_thuc": date(2025, 9, 30),
                "ghi_chu": f"Nua ky dau - {ten_hp}"
            }
            # Schedule 2: Second half (2025-10-01 to 2025-11-15)
            sch2_detail = {
                "ma_lich": f"LH_{info['code']}_{ma_hp}_{nhom_str}_S2",
                "ma_lop_hp": ma_lop_hp,
                "ma_phong": ma_phong,
                "thu_trong_tuan": day,
                "tiet_bat_dau": tiet,
                "so_tiet": so_tiet_s2,
                "ngay_bat_dau": date(2025, 10, 1),
                "ngay_ket_thuc": date(2025, 11, 15),
                "ghi_chu": f"Nua ky sau - {ten_hp}"
            }
            schedules_data[site].append(sch1_detail)
            schedules_data[site].append(sch2_detail)

# 2. SQL Statements
semester_sql = text("""
    INSERT INTO "HocKy" ("MaHocKy", "NamHoc", "KySo", "NgayBatDau", "NgayKetThuc", "TrangThaiHocKy")
    VALUES (:ma_hoc_ky, :nam_hoc, :ky_so, :ngay_bd, :ngay_kt, :trang_thai)
    ON CONFLICT ("MaHocKy") DO UPDATE
    SET "NamHoc" = EXCLUDED."NamHoc",
        "KySo" = EXCLUDED."KySo",
        "NgayBatDau" = EXCLUDED."NgayBatDau",
        "NgayKetThuc" = EXCLUDED."NgayKetThuc",
        "TrangThaiHocKy" = EXCLUDED."TrangThaiHocKy";
""")

user_sql = text("""
    INSERT INTO "users" ("userId", "username", "password", "email", "role", "MaCoSo", "status", "NgayTao")
    VALUES (:user_id, :username, :password, :email, :role, :branch, :status, :created_at)
    ON CONFLICT ("userId") DO UPDATE
    SET "username" = EXCLUDED."username",
        "password" = EXCLUDED."password",
        "email" = EXCLUDED."email",
        "role" = EXCLUDED."role",
        "MaCoSo" = EXCLUDED."MaCoSo",
        "status" = EXCLUDED."status";
""")

classroom_sql = text("""
    INSERT INTO "PhongHoc" ("MaPhong", "TenPhong", "ToaNha", "Tang", "SucChua", "LoaiPhong", "MaCoSo", "TrangThai", "NgayTao")
    VALUES (:ma_phong, :ten_phong, :toa_nha, :tang, :suc_chua, :loai_phong, :ma_coso, :trang_thai, NOW())
    ON CONFLICT ("MaPhong") DO UPDATE
    SET "TenPhong" = EXCLUDED."TenPhong",
        "ToaNha" = EXCLUDED."ToaNha",
        "Tang" = EXCLUDED."Tang",
        "SucChua" = EXCLUDED."SucChua",
        "LoaiPhong" = EXCLUDED."LoaiPhong",
        "MaCoSo" = EXCLUDED."MaCoSo",
        "TrangThai" = EXCLUDED."TrangThai";
""")

section_sql = text("""
    INSERT INTO "LopHocPhan" ("MaLopHP", "MaHP", "MaHocKy", "MaCoSo", "MaGV", "TenLopHP", "SiSoToiDa", "SiSoHienTai", "HinhThucHoc", "TrangThaiLop", "NgayTao")
    VALUES (:ma_lop_hp, :ma_hp, :ma_hoc_ky, :ma_coso, :ma_gv, :ten_lop_hp, :si_so_toi_da, :si_so_hien_tai, :hinh_thuc_hoc, :trang_thai_lop, NOW())
    ON CONFLICT ("MaLopHP") DO UPDATE
    SET "MaHP" = EXCLUDED."MaHP",
        "MaHocKy" = EXCLUDED."MaHocKy",
        "MaCoSo" = EXCLUDED."MaCoSo",
        "MaGV" = EXCLUDED."MaGV",
        "TenLopHP" = EXCLUDED."TenLopHP",
        "SiSoToiDa" = EXCLUDED."SiSoToiDa",
        "SiSoHienTai" = EXCLUDED."SiSoHienTai",
        "HinhThucHoc" = EXCLUDED."HinhThucHoc",
        "TrangThaiLop" = EXCLUDED."TrangThaiLop";
""")

schedule_sql = text("""
    INSERT INTO "LichHoc" ("MaLich", "MaLopHP", "MaPhong", "ThuTrongTuan", "TietBatDau", "SoTiet", "NgayBatDau", "NgayKetThuc", "GhiChu")
    VALUES (:ma_lich, :ma_lop_hp, :ma_phong, :thu_trong_tuan, :tiet_bat_dau, :so_tiet, :ngay_bat_dau, :ngay_ket_thuc, :ghi_chu)
    ON CONFLICT ("MaLich") DO UPDATE
    SET "MaLopHP" = EXCLUDED."MaLopHP",
        "MaPhong" = EXCLUDED."MaPhong",
        "ThuTrongTuan" = EXCLUDED."ThuTrongTuan",
        "TietBatDau" = EXCLUDED."TietBatDau",
        "SoTiet" = EXCLUDED."SoTiet",
        "NgayBatDau" = EXCLUDED."NgayBatDau",
        "NgayKetThuc" = EXCLUDED."NgayKetThuc",
        "GhiChu" = EXCLUDED."GhiChu";
""")

student_sql = text("""
    INSERT INTO "SinhVien" ("MaSV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayNhapHoc", "NgayTao")
    VALUES (:ma_sv, :user_id, :ho, :ten, :ngay_sinh, :gioi_tinh, :sdt, :dia_chi, :ma_coso, :ma_khoa, :trang_thai, :ngay_nhap_hoc, :ngay_tao)
    ON CONFLICT ("MaSV") DO UPDATE
    SET "userId" = EXCLUDED."userId",
        "Ho" = EXCLUDED."Ho",
        "Ten" = EXCLUDED."Ten",
        "NgaySinh" = EXCLUDED."NgaySinh",
        "GioiTinh" = EXCLUDED."GioiTinh",
        "SDT" = EXCLUDED."SDT",
        "DiaChi" = EXCLUDED."DiaChi",
        "MaCoSo" = EXCLUDED."MaCoSo",
        "MaKhoa" = EXCLUDED."MaKhoa",
        "TrangThai" = EXCLUDED."TrangThai",
        "NgayNhapHoc" = EXCLUDED."NgayNhapHoc";
""")

teacher_sql = text("""
    INSERT INTO "GiangVien" ("MaGV", "userId", "Ho", "Ten", "NgaySinh", "GioiTinh", "HocVi", "HocHam", "SDT", "DiaChi", "MaCoSo", "MaKhoa", "TrangThai", "NgayVaoLam", "NgayTao")
    VALUES (:ma_gv, :user_id, :ho, :ten, :ngay_sinh, :gioi_tinh, :hoc_vi, :hoc_ham, :sdt, :dia_chi, :ma_coso, :ma_khoa, :trang_thai, :ngay_vao_lam, :ngay_tao)
    ON CONFLICT ("MaGV") DO UPDATE
    SET "userId" = EXCLUDED."userId",
        "Ho" = EXCLUDED."Ho",
        "Ten" = EXCLUDED."Ten",
        "NgaySinh" = EXCLUDED."NgaySinh",
        "GioiTinh" = EXCLUDED."GioiTinh",
        "HocVi" = EXCLUDED."HocVi",
        "HocHam" = EXCLUDED."HocHam",
        "SDT" = EXCLUDED."SDT",
        "DiaChi" = EXCLUDED."DiaChi",
        "MaCoSo" = EXCLUDED."MaCoSo",
        "MaKhoa" = EXCLUDED."MaKhoa",
        "TrangThai" = EXCLUDED."TrangThai",
        "NgayVaoLam" = EXCLUDED."NgayVaoLam";
""")

course_sql = text("""
    INSERT INTO "HocPhan" ("MaHP", "TenHP", "SoTinChi", "SoTietLyThuyet", "SoTietThucHanh", "LoaiHocPhan", "MaKhoa", "MoTa", "TrangThai", "NgayTao")
    VALUES (:ma_hp, :ten_hp, :so_tc, :so_tiet_lt, :so_tiet_th, :loai_hp, :ma_khoa, :mo_ta, :trang_thai, NOW())
    ON CONFLICT ("MaHP") DO UPDATE
    SET "TenHP" = EXCLUDED."TenHP",
        "SoTinChi" = EXCLUDED."SoTinChi",
        "SoTietLyThuyet" = EXCLUDED."SoTietLyThuyet",
        "SoTietThucHanh" = EXCLUDED."SoTietThucHanh",
        "LoaiHocPhan" = EXCLUDED."LoaiHocPhan",
        "MaKhoa" = EXCLUDED."MaKhoa",
        "MoTa" = EXCLUDED."MoTa",
        "TrangThai" = EXCLUDED."TrangThai";
""")

# 3. Execute
for site, engine in engines.items():
    print(f"Cleaning & Seeding {site}...")
    try:
        with engine.begin() as conn:
            # Bypass replication / constraint triggers temporarily
            try:
                conn.execute(text("SET session_replication_role = replica;"))
            except Exception:
                pass
                
            # Truncate tables to ensure fresh state
            conn.execute(text('TRUNCATE TABLE "SinhVien", "GiangVien", "users", "PhongHoc", "LopHocPhan", "LichHoc", "HocKy" CASCADE;'))
            print("  [v] Truncated old semesters, users, students, teachers, classrooms, class sections, and schedules")

            # Seed Semester
            conn.execute(semester_sql, semester_detail)
            print("  [v] Seeded Semester HK2-2025")

            # Seed Admin
            conn.execute(user_sql, admin_detail)
            print("  [v] Seeded Admin account")

            # Seed Users
            inserted_users = 0
            for u in users_data:
                conn.execute(user_sql, u)
                inserted_users += 1
            print(f"  [v] Seeded {inserted_users} users (shared table)")

            # Seed local Students
            inserted_students = 0
            for sv in students_data[site]:
                conn.execute(student_sql, sv)
                inserted_students += 1
            print(f"  [v] Seeded {inserted_students} local students (partitioned table)")

            # Seed local Teachers
            inserted_teachers = 0
            for gv in teachers_data[site]:
                conn.execute(teacher_sql, gv)
                inserted_teachers += 1
            print(f"  [v] Seeded {inserted_teachers} local teachers (partitioned table)")
            
            # Seed shared courses (HocPhan)
            inserted_courses = 0
            for c in courses_data:
                conn.execute(course_sql, c)
                inserted_courses += 1
            print(f"  [v] Seeded {inserted_courses} common courses (replicated table)")

            # Seed local Classrooms
            inserted_rooms = 0
            for r in classrooms_data[site]:
                conn.execute(classroom_sql, r)
                inserted_rooms += 1
            print(f"  [v] Seeded {inserted_rooms} local classrooms (partitioned table)")

            # Seed local Class Sections
            inserted_sections = 0
            for sec in sections_data[site]:
                conn.execute(section_sql, sec)
                inserted_sections += 1
            print(f"  [v] Seeded {inserted_sections} local class sections (partitioned table)")

            # Seed local Schedules
            inserted_schedules = 0
            for sch in schedules_data[site]:
                conn.execute(schedule_sql, sch)
                inserted_schedules += 1
            print(f"  [v] Seeded {inserted_schedules} local schedules (partitioned table)")

            try:
                conn.execute(text("SET session_replication_role = DEFAULT;"))
            except Exception:
                pass
                
    except Exception as e:
        print(f"  [x] Failed to seed database for site {site}: {e}")


import subprocess

# Determine docker directory relative to this script
docker_dir = os.path.join(os.path.dirname(__file__), "..", "docker")

# Run bootstrap script in backend container
print(f"Running bootstrap_search.py inside backend container...")
res_bootstrap = subprocess.run([
    "docker", "compose", "exec", "-T", "backend",
    "python", "scripts/bootstrap_search.py", "--force", "--host", "http://elasticsearch:9200"
], cwd=docker_dir)
if res_bootstrap.returncode == 0:
    print("Elasticsearch bootstrap completed successfully.")
else:
    print(f"Elasticsearch bootstrap failed with exit code: {res_bootstrap.returncode}")
    
# Run reindex script in backend container
print(f"Running reindex_es.py inside backend container...")
res_reindex = subprocess.run([
    "docker", "compose", "exec", "-T", "backend",
    "sh", "-c", "ES_HOST=http://elasticsearch:9200 PG_HOST=postgres_hadong python scripts/reindex_es.py"
], cwd=docker_dir)
if res_reindex.returncode == 0:
    print("Elasticsearch reindexing completed successfully.")
else:
    print(f"Elasticsearch reindexing failed with exit code: {res_reindex.returncode}")
