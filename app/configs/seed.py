from datetime import datetime

from sqlalchemy import text

from configs.config import pwd_context
from configs.db import SessionLocals


def seed_common_data(db):
    """Seed common reference data."""
    # DO NOT truncate. Let ON CONFLICT handle updates.

    branch_data = [
        (
            "HADONG",
            "Co so Ha Dong",
            "So 10 Tran Phu, Ha Dong, Ha Noi",
            "024.12345678",
            "hadong@ptit.edu.vn",
            "1997-08-15",
            "HoatDong",
        ),
        (
            "HOALAC",
            "Co so Hoa Lac",
            "Khu cong nghe cao Hoa Lac, Thach That, Ha Noi",
            "024.87654321",
            "hoalac@ptit.edu.vn",
            "2018-09-01",
            "HoatDong",
        ),
        (
            "NGOCTRUC",
            "Co so Ngoc Truc",
            "Dai Mo, Nam Tu Liem, Ha Noi",
            "024.11112222",
            "ngoctruc@ptit.edu.vn",
            "2023-01-01",
            "HoatDong",
        ),
    ]

    for code, name, address, phone, email, established_date, status in branch_data:
        insert_sql = text(
            """
            INSERT INTO "CoSo" ("MaCoSo", "TenCoSo", "DiaChi", "SoDienThoai", "Email", "NgayThanhLap", "TrangThai")
            VALUES (:code, :name, :address, :phone, :email, :established_date, :status)
            ON CONFLICT ("MaCoSo") DO UPDATE SET
                "TenCoSo" = EXCLUDED."TenCoSo",
                "DiaChi" = EXCLUDED."DiaChi",
                "SoDienThoai" = EXCLUDED."SoDienThoai",
                "Email" = EXCLUDED."Email",
                "NgayThanhLap" = EXCLUDED."NgayThanhLap",
                "TrangThai" = EXCLUDED."TrangThai"
            """
        )
        db.execute(
            insert_sql,
            {
                "code": code,
                "name": name,
                "address": address,
                "phone": phone,
                "email": email,
                "established_date": established_date,
                "status": status,
            },
        )

    department_data = [
        ("CNTT", "Cong nghe thong tin", "Khoa CNTT - Vien CNTT&TT", "1997-08-15", "HoatDong"),
        ("DPT", "Da phuong tien", "Khoa Thiet ke va Sang tao noi dung so", "2005-09-01", "HoatDong"),
        ("VT", "Vien thong", "Khoa Ky thuat Vien thong", "1997-08-15", "HoatDong"),
    ]

    for code, name, description, established_date, status in department_data:
        insert_sql = text(
            """
            INSERT INTO "Khoa" ("MaKhoa", "TenKhoa", "MoTa", "NgayThanhLap", "TrangThai")
            VALUES (:code, :name, :description, :established_date, :status)
            ON CONFLICT ("MaKhoa") DO UPDATE SET
                "TenKhoa" = EXCLUDED."TenKhoa",
                "MoTa" = EXCLUDED."MoTa",
                "NgayThanhLap" = EXCLUDED."NgayThanhLap",
                "TrangThai" = EXCLUDED."TrangThai"
            """
        )
        db.execute(
            insert_sql,
            {
                "code": code,
                "name": name,
                "description": description,
                "established_date": established_date,
                "status": status,
            },
        )

    db.commit()


def seed_admin(sessions):
    """Seed the default admin account on every site."""
    admin_id = "ADMIN1"
    username = "admin"
    hashed_password = pwd_context.hash("admin123")

    for site, session_factory in sessions.items():
        db = session_factory()
        try:
            exists = text('SELECT 1 FROM "users" WHERE "username" = :username')
            if not db.execute(exists, {"username": username}).fetchone():
                insert_sql = text(
                    """
                    INSERT INTO "users" ("userId", "username", "password", "role", "email", "MaCoSo", "status", "NgayTao")
                    VALUES (:user_id, :username, :password, :role, :email, :branch_code, :status, :created_at)
                    """
                )
                db.execute(
                    insert_sql,
                    {
                        "user_id": admin_id,
                        "username": username,
                        "password": hashed_password,
                        "role": "Admin",
                        "email": "admin@system.com",
                        "branch_code": "HADONG",
                        "status": "Active",
                        "created_at": datetime.now().isoformat(),
                    },
                )
                db.commit()
                print(f"[{site}] Default admin created.")
        finally:
            db.close()


def seed_all():
    """Seed data for all sites."""
    sessions = SessionLocals

    for _, session_factory in sessions.items():
        db = session_factory()
        try:
            seed_common_data(db)
        finally:
            db.close()

    seed_admin(sessions)
    print("System initialization complete.")


if __name__ == "__main__":
    seed_all()
