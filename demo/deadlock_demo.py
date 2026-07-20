import sys
import os
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
import json
from sqlalchemy import text
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from configs.db import SessionLocals
from services.AuthService import AuthService

DEMO_MA_SV = ["SVHD26CNTT001", "SVHD26CNTT002"]

def login(ma_sv: str):
    """Lấy user object từ DB theo MaSV (username = MaSV)."""
    user = AuthService._find_user_by_username(ma_sv)
    if not user:
        raise Exception(f"Không tìm thấy tài khoản: {ma_sv}")
    return user

def reset_database_for_swap(class_a, class_b, user_ids, users):
    """Reset sĩ số hai lớp và thiết lập đăng ký ban đầu để chuẩn bị đổi lớp qua lại."""
    
    with SessionLocals['HOALAC']() as session:
        row = session.execute(
            text('SELECT "MaHP", "MaHocKy" FROM "LopHocPhan" WHERE "MaLopHP" = :c'),
            {"c": class_a}
        ).fetchone()
        ma_hp, ma_hk = row[0], row[1]

    # 2. Reset sĩ số hai lớp về 1/50
        session.execute(
            text('UPDATE "LopHocPhan" SET "SiSoHienTai" = 1, "SiSoToiDa" = 50 WHERE "MaLopHP" IN (:a, :b)'),
            {"a": class_a, "b": class_b}
        )
        session.commit()

    # 3. Xóa tất cả đăng ký của 2 sinh viên này trên tất cả các site
    # để tránh trùng lịch học (schedule conflict) và trùng môn học với các lớp khác
    params = {"ids": user_ids}
    for session_factory in SessionLocals.values():
        with session_factory() as session:
            session.execute(
                text('DELETE FROM "DangKy" WHERE "userId" = ANY(:ids)'),
                params
            )
            session.execute(
                text('DELETE FROM "DangKy_ChuyenCoSo" WHERE "userId" = ANY(:ids)'),
                params
            )
            session.commit()

    # 4. Tạo đăng ký ban đầu: SV1 ở class_a, SV2 ở class_b tại site HOALAC
    with SessionLocals['HOALAC']() as session:
        session.execute(
            text("""
                INSERT INTO "DangKy" ("userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy")
                VALUES (:user_id, :ma_sv, :ma_lop, :ma_hp, :ma_hk, NOW(), 'DaDangKy', 1)
            """),
            {"user_id": users[0].userId, "ma_sv": users[0].username, "ma_lop": class_a, "ma_hp": ma_hp, "ma_hk": ma_hk}
        )
       
        session.execute(
            text("""
                INSERT INTO "DangKy" ("userId", "MaSV", "MaLopHP", "MaHP", "MaHocKy", "NgayDangKy", "TrangThaiDangKy", "LanDangKy")
                VALUES (:user_id, :ma_sv, :ma_lop, :ma_hp, :ma_hk, NOW(), 'DaDangKy', 1)
            """),
            {"user_id": users[1].userId, "ma_sv": users[1].username, "ma_lop": class_b, "ma_hp": ma_hp, "ma_hk": ma_hk}
        )
        session.commit()

def register_thread(user, class_code):
    """Luồng đăng ký cho 1 sinh viên qua HTTP API của backend."""
    try:
        # 1. Đăng nhập
        login_data = urllib.parse.urlencode({
            "username": user.username,
            "password": "123456"
        }).encode("utf-8")
        
        login_req = urllib.request.Request(
            "http://localhost:8000/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        with urllib.request.urlopen(login_req) as login_res:
            token_info = json.loads(login_res.read().decode("utf-8"))
            token = token_info["access_token"]
            
        # 2. đăng ký/đổi lớp học phần
        register_data = json.dumps({"MaLopHP": class_code}).encode("utf-8")
        register_req = urllib.request.Request(
            "http://localhost:8000/enrollments/register",
            data=register_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        with urllib.request.urlopen(register_req) as register_res:
            result = json.loads(register_res.read().decode("utf-8"))
            print(f"SV {user.username} dang ky: success={result.get('success')} - {result.get('message')}")
            
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            print(f"SV {user.username} dang ky that bai: {err_data.get('message')} - Chi tiet: {err_data.get('errorr')}")
        except Exception:
            print(f"SV {user.username} loi HTTP: {e.code} - {e.reason}")
    except Exception as e:
        print(f"SV {user.username} loi he thong: {e}")

def main():
    try:
        # 1. Đăng nhập
        users = [login(ma_sv) for ma_sv in DEMO_MA_SV]

        # 2. Tìm môn học
        with SessionLocals['HOALAC']() as session:
            row = session.execute(
                text("""
                    SELECT "MaHP", "MaHocKy"
                    FROM "LopHocPhan"
                    WHERE "MaCoSo" = 'HOALAC'
                    GROUP BY "MaHP", "MaHocKy"
                    HAVING COUNT("MaLopHP") >= 2
                    LIMIT 1
                """)
            ).fetchone()
            if not row:
                raise Exception("Không tìm thấy môn học nào có từ 2 lớp trở lên ở HOALAC")
            ma_hp, ma_hk = row[0], row[1]
            
            rows = session.execute(
                text("""
                    SELECT "MaLopHP"
                    FROM "LopHocPhan"
                    WHERE "MaHP" = :ma_hp AND "MaHocKy" = :ma_hk AND "MaCoSo" = 'HOALAC'
                    LIMIT 2
                """),
                {"ma_hp": ma_hp, "ma_hk": ma_hk}
            ).fetchall()
            class_a = rows[0][0]
            class_b = rows[1][0]

        # 3. Reset DB và thiết lập đăng ký ban đầu
        reset_database_for_swap(class_a, class_b, [u.userId for u in users], users)

        # 4. Đổi lớp đồng thời
        threads = [
            threading.Thread(target=register_thread, args=(users[0], class_b)),
            threading.Thread(target=register_thread, args=(users[1], class_a))
        ]
        for t in threads: t.start()
        for t in threads: t.join()
        
        print(1)
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == '__main__':
    main()
