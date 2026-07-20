import json
import re
import time
from datetime import datetime

import psycopg2


CENTRALIZED_DSN = {
    "host": "localhost",
    "port": 5435,
    "dbname": "csdlpt_centralized",
    "user": "csdlpt_user",
    "password": "csdlpt_pass",
}

DISTRIBUTED_DSN = {
    "host": "localhost",
    "port": 5432,
    "dbname": "csdlpt_hadong",
    "user": "csdlpt_user",
    "password": "csdlpt_pass",
}

RESULT_DSN = CENTRALIZED_DSN


BENCHMARK_QUERIES = [
    {
        "code": "Q1",
        "name": "Danh sách lớp học phần theo cơ sở HADONG",
        "type": "Local",
        "used_fdw": False,
        "centralized_sql": """
            SELECT lhp."MaLopHP", lhp."MaHP", lhp."MaGV", lhp."SiSoToiDa", lhp."MaHocKy",
                   hp."TenHP", hp."SoTietLyThuyet", hp."SoTietThucHanh"
            FROM "LopHocPhan" lhp
            JOIN "HocPhan" hp ON lhp."MaHP" = hp."MaHP"
            WHERE lhp."MaCoSo" = 'HADONG'
            ORDER BY lhp."MaLopHP";
        """,
        "distributed_sql": """
            SELECT lhp."MaLopHP", lhp."MaHP", lhp."MaGV", lhp."SiSoToiDa", lhp."MaHocKy",
                   hp."TenHP", hp."SoTietLyThuyet", hp."SoTietThucHanh"
            FROM "LopHocPhan" lhp
            JOIN "HocPhan" hp ON lhp."MaHP" = hp."MaHP"
            WHERE lhp."MaCoSo" = 'HADONG'
            ORDER BY lhp."MaLopHP";
        """,
    },
    {
        "code": "Q2",
        "name": "Thống kê số sinh viên theo từng cơ sở",
        "type": "Global",
        "used_fdw": True,
        "centralized_sql": """
            SELECT "MaCoSo", COUNT(*) AS "TongSinhVien"
            FROM "SinhVien"
            GROUP BY "MaCoSo"
            ORDER BY "MaCoSo";
        """,
        "distributed_sql": """
            SELECT "MaCoSo", COUNT(*) AS "TongSinhVien"
            FROM "vw_sinhvien_toantruong"
            GROUP BY "MaCoSo"
            ORDER BY "MaCoSo";
        """,
    },
    {
        "code": "Q3",
        "name": "Thống kê tỉ lệ lấp đầy lớp học phần toàn trường",
        "type": "Global",
        "used_fdw": True,
        "centralized_sql": """
            SELECT
            lhp."MaCoSo",
            COUNT(*) AS "TongLop",
            SUM(lhp."SiSoHienTai") AS "TongSV_DK",
            SUM(lhp."SiSoToiDa") AS "TongSucChua",
            ROUND(
                SUM(lhp."SiSoHienTai")::NUMERIC / NULLIF(SUM(lhp."SiSoToiDa"), 0) * 100,
                2
            ) AS "TyLeLopDay_Percent"
            FROM "LopHocPhan" lhp
            GROUP BY lhp."MaCoSo"
            ORDER BY lhp."MaCoSo";
        """,
        "distributed_sql": """
            SELECT
            lhp."MaCoSo",
            COUNT(*) AS "TongLop",
            SUM(lhp."SiSoHienTai") AS "TongSV_DK",
            SUM(lhp."SiSoToiDa") AS "TongSucChua",
            ROUND(
                SUM(lhp."SiSoHienTai")::NUMERIC / NULLIF(SUM(lhp."SiSoToiDa"), 0) * 100,
                2
            ) AS "TyLeLopDay_Percent"
            FROM "vw_lophocphan_toantruong" lhp
            GROUP BY lhp."MaCoSo"
            ORDER BY lhp."MaCoSo";
        """,
    },
    {
        "code": "Q4",
        "name": "Danh sách sinh viên đăng ký chéo cơ sở",
        "type": "Global Join",
        "used_fdw": True,
        "centralized_sql": """
            SELECT
                dk."MaDangKy",
                sv."MaSV",
                sv."Ten" AS "HoTen",
                sv."MaCoSo" AS "CoSoSinhVien",
                lhp."MaLopHP",
                lhp."MaCoSo" AS "CoSoLopHocPhan",
                dk."NgayDangKy"
            FROM "DangKy" dk
            JOIN "SinhVien" sv ON dk."MaSV" = sv."MaSV"
            JOIN "LopHocPhan" lhp ON dk."MaLopHP" = lhp."MaLopHP"
            WHERE sv."MaCoSo" <> lhp."MaCoSo"
            ORDER BY dk."NgayDangKy" DESC
            LIMIT 20;
        """,
        "distributed_sql": """
            SELECT
                dk."MaDangKy",
                sv."MaSV",
                sv."Ten" AS "HoTen",
                sv."MaCoSo" AS "CoSoSinhVien",
                lhp."MaLopHP",
                lhp."MaCoSo" AS "CoSoLopHocPhan",
                dk."NgayDangKy"
            FROM "vw_dangky_toantruong" dk
            JOIN "vw_sinhvien_toantruong" sv ON dk."MaSV" = sv."MaSV"
            JOIN "vw_lophocphan_toantruong" lhp ON dk."MaLopHP" = lhp."MaLopHP"
            WHERE sv."MaCoSo" <> lhp."MaCoSo"
            ORDER BY dk."NgayDangKy" DESC
            LIMIT 20;
        """,
    },
    {
        "code": "Q5",
        "name": "Học phần có nhiều sinh viên đăng ký nhất toàn trường",
        "type": "Global Join",
        "used_fdw": True,
        "centralized_sql": """
            SELECT
                hp."MaHP",
                hp."TenHP",
                COUNT(dk."MaDangKy") AS "SoLuotDangKy"
            FROM "DangKy" dk
            JOIN "LopHocPhan" lhp ON dk."MaLopHP" = lhp."MaLopHP"
            JOIN "HocPhan" hp ON lhp."MaHP" = hp."MaHP"
            WHERE dk."TrangThaiDangKy" = 'DaDangKy'
            GROUP BY hp."MaHP", hp."TenHP"
            ORDER BY "SoLuotDangKy" DESC
            LIMIT 10;
        """,
        "distributed_sql": """
            SELECT
                hp."MaHP",
                hp."TenHP",
                COUNT(dk."MaDangKy") AS "SoLuotDangKy"
            FROM "vw_dangky_toantruong" dk
            JOIN "vw_lophocphan_toantruong" lhp ON dk."MaLopHP" = lhp."MaLopHP"
            JOIN "HocPhan" hp ON lhp."MaHP" = hp."MaHP"
            WHERE dk."TrangThaiDangKy" = 'DaDangKy'
            GROUP BY hp."MaHP", hp."TenHP"
            ORDER BY "SoLuotDangKy" DESC
            LIMIT 10;
        """,
    },
    {
        "code": "Q6",
        "name": "Sĩ số từng lớp học phần tại HADONG",
        "type": "Local",
        "used_fdw": False,
        "centralized_sql": """
            SELECT
                lhp."MaLopHP",
                lhp."SiSoToiDa",
                COUNT(dk."MaDangKy") AS "SiSoHienTai"
            FROM "LopHocPhan" lhp
            LEFT JOIN "DangKy" dk ON lhp."MaLopHP" = dk."MaLopHP"
                AND dk."TrangThaiDangKy" = 'DaDangKy'
            WHERE lhp."MaCoSo" = 'HADONG'
            GROUP BY lhp."MaLopHP", lhp."SiSoToiDa"
            ORDER BY lhp."MaLopHP";
        """,
        "distributed_sql": """
            SELECT
                lhp."MaLopHP",
                lhp."SiSoToiDa",
                COUNT(dk."MaDangKy") AS "SiSoHienTai"
            FROM "LopHocPhan" lhp
            LEFT JOIN "DangKy" dk ON lhp."MaLopHP" = dk."MaLopHP"
                AND dk."TrangThaiDangKy" = 'DaDangKy'
            WHERE lhp."MaCoSo" = 'HADONG'
            GROUP BY lhp."MaLopHP", lhp."SiSoToiDa"
            ORDER BY lhp."MaLopHP";
        """,
    },
    {
        "code": "Q7",
        "name": "Thống kê đăng ký theo học kỳ",
        "type": "Global Join",
        "used_fdw": True,
        "centralized_sql": """
           SELECT
            hk."MaHocKy",
            hk."NamHoc",
            hk."KySo",
            hk."TrangThaiHocKy",
        COUNT(DISTINCT lhp."MaLopHP") AS "TongLopHP",
        COUNT(DISTINCT dk."MaDangKy") AS "TongDangKy"
        FROM "HocKy" hk
        LEFT JOIN "LopHocPhan" lhp ON hk."MaHocKy" = lhp."MaHocKy"
        LEFT JOIN "DangKy" dk ON lhp."MaLopHP" = dk."MaLopHP" AND dk."TrangThaiDangKy" = 'DaDangKy'
        GROUP BY hk."MaHocKy", hk."NamHoc", hk."KySo", hk."TrangThaiHocKy"
        ORDER BY hk."NamHoc" DESC, hk."KySo";
        """,
        "distributed_sql": """
            SELECT
                hk."MaHocKy",
                hk."NamHoc",
                hk."KySo",
                hk."TrangThaiHocKy",
            COUNT(DISTINCT lhp."MaLopHP") AS "TongLopHP",
            COUNT(DISTINCT dk."MaDangKy") AS "TongDangKy"
            FROM "HocKy" hk
            LEFT JOIN "vw_lophocphan_toantruong" lhp ON hk."MaHocKy" = lhp."MaHocKy"
            LEFT JOIN "vw_dangky_toantruong" dk ON lhp."MaLopHP" = dk."MaLopHP" AND dk."TrangThaiDangKy" = 'DaDangKy'
            GROUP BY hk."MaHocKy", hk."NamHoc", hk."KySo", hk."TrangThaiHocKy"
            ORDER BY hk."NamHoc" DESC, hk."KySo";
        """,
    },
]


def connect(dsn: dict):
    return psycopg2.connect(**dsn)


def parse_explain_json(raw_value):
    if isinstance(raw_value, str):
        return json.loads(raw_value)
    return raw_value


def run_explain(conn, sql: str):
    explain_sql = f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        {sql}
    """

    with conn.cursor() as cur:
        cur.execute(explain_sql)
        raw = cur.fetchone()[0]

    explain_data = parse_explain_json(raw)
    root = explain_data[0]
    plan = root["Plan"]

    execution_time_ms = float(root.get("Execution Time", 0.0))
    planning_time_ms = float(root.get("Planning Time", 0.0))
    rows_returned = int(plan.get("Actual Rows", 0))

    return {
        "execution_time_ms": execution_time_ms,
        "planning_time_ms": planning_time_ms,
        "total_time_ms": execution_time_ms + planning_time_ms,
        "rows_returned": rows_returned,
    }


def create_run(conn):
    label = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO benchmark_run (run_label, dataset_note)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                label,
                "Centralized vs Distributed benchmark; measured by EXPLAIN ANALYZE FORMAT JSON",
            ),
        )
        run_id = cur.fetchone()[0]

    conn.commit()
    return run_id, label


def insert_result(conn, run_id, query, model, measured):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO benchmark_result (
                run_id,
                query_code,
                query_name,
                query_type,
                model,
                execution_time_ms,
                planning_time_ms,
                total_time_ms,
                used_fdw,
                rows_returned
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                run_id,
                query["code"],
                query["name"],
                query["type"],
                model,
                measured["execution_time_ms"],
                measured["planning_time_ms"],
                measured["total_time_ms"],
                query["used_fdw"] if model == "distributed" else False,
                measured["rows_returned"],
            ),
        )

    conn.commit()


def main():
    with connect(RESULT_DSN) as result_conn:
        run_id, label = create_run(result_conn)

        print(f"Created benchmark run: {label} | run_id={run_id}")

        with connect(CENTRALIZED_DSN) as centralized_conn, connect(DISTRIBUTED_DSN) as distributed_conn:
            for query in BENCHMARK_QUERIES:
                print(f"Running {query['code']} centralized...")
                centralized_result = run_explain(centralized_conn, query["centralized_sql"])
                insert_result(result_conn, run_id, query, "centralized", centralized_result)

                print(f"Running {query['code']} distributed...")
                distributed_result = run_explain(distributed_conn, query["distributed_sql"])
                insert_result(result_conn, run_id, query, "distributed", distributed_result)

                print(
                    f"{query['code']} | "
                    f"centralized={centralized_result['execution_time_ms']:.3f} ms | "
                    f"distributed={distributed_result['execution_time_ms']:.3f} ms"
                )

    print("Done. Open Grafana dashboard to view results.")


if __name__ == "__main__":
    main()