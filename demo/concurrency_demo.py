import sys
import os
import threading
import urllib.request
import urllib.parse
import urllib.error
import json
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from configs.db import SessionLocals
from services.EnrollmentService import EnrollmentService
from services.AuthService import AuthService
from schemas.Enrollment import EnrollmentCreate

# Hai sinh viên cố định cho demo — username & password đều là MaSV
DEMO_MA_SV = ["SVHD26CNTT001", "SVHD26CNTT002"]

def login(ma_sv: str):
    """Lấy user object từ DB theo MaSV (username = MaSV)."""
    user = AuthService._find_user_by_username(ma_sv)
    if not user:
        raise Exception(f"Không tìm thấy tài khoản: {ma_sv}")
    return user

def reset_database(class_code, user_ids):
    """Reset sĩ số lớp về 49/50 và xóa bản ghi đăng ký cũ của 2 sinh viên."""
    site = class_code.split("_")[0].upper()
    with SessionLocals[site]() as session:
        session.execute(
            text('UPDATE "LopHocPhan" SET "SiSoHienTai" = 49, "SiSoToiDa" = 50 WHERE "MaLopHP" = :c'),
            {"c": class_code}
        )
        session.commit()

    params = {"ids": user_ids}
    for session_factory in SessionLocals.values():
        with session_factory() as session:
            session.execute(text('DELETE FROM "DangKy" WHERE "userId" = ANY(:ids)'), params)
            session.execute(text('DELETE FROM "DangKy_ChuyenCoSo" WHERE "userId" = ANY(:ids)'), params)
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
            
        # 2. Đăng ký học phần
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
            print(f"SV {user.username} dang ky {class_code}: success={result.get('success')} - {result.get('message')}")
            
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
        # 1. Đăng nhập 2 sinh viên
        users = [login(ma_sv) for ma_sv in DEMO_MA_SV]

        # 2. Lấy lớp học phần mẫu ở HOALAC
        with SessionLocals['HOALAC']() as session:
            row = session.execute(
                text('SELECT "MaLopHP" FROM "LopHocPhan" WHERE "MaCoSo" = \'HOALAC\' LIMIT 1')
            ).fetchone()
        if not row:
            raise Exception("Khong tim thay lop hoc phan o HOALAC")
        class_code = row[0]

        # 3. Reset DB về trạng thái ban đầu (49/50)
        reset_database(class_code, [u.userId for u in users])

        # 4. Chạy 2 luồng đăng ký đồng thời
        threads = [threading.Thread(target=register_thread, args=(u, class_code)) for u in users]
        for t in threads: t.start()
        for t in threads: t.join()

    except Exception as e:
        print(f"Loi: {e}")

if __name__ == '__main__':
    main()
