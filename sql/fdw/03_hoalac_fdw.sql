CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SCHEMA IF EXISTS fdw_hadong CASCADE;
DROP SCHEMA IF EXISTS fdw_ngoctruc CASCADE;
DROP SERVER IF EXISTS hadong_server CASCADE;
DROP SERVER IF EXISTS ngoctruc_server CASCADE;

CREATE SCHEMA fdw_hadong;
CREATE SCHEMA fdw_ngoctruc;

CREATE SERVER hadong_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_hadong', dbname 'csdlpt_hadong', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER hadong_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

CREATE SERVER ngoctruc_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_ngoctruc', dbname 'csdlpt_ngoctruc', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER ngoctruc_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER hadong_server
INTO fdw_hadong;

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER ngoctruc_server
INTO fdw_ngoctruc;
