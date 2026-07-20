CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SCHEMA IF EXISTS fdw_ngoctruc CASCADE;
DROP SCHEMA IF EXISTS fdw_hoalac CASCADE;
DROP SERVER IF EXISTS ngoctruc_server CASCADE;
DROP SERVER IF EXISTS hoalac_server CASCADE;

CREATE SCHEMA fdw_ngoctruc;
CREATE SCHEMA fdw_hoalac;

CREATE SERVER ngoctruc_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_ngoctruc', dbname 'csdlpt_ngoctruc', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER ngoctruc_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

CREATE SERVER hoalac_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_hoalac', dbname 'csdlpt_hoalac', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER hoalac_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER ngoctruc_server
INTO fdw_ngoctruc;

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER hoalac_server
INTO fdw_hoalac;
