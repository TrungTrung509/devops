CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SCHEMA IF EXISTS fdw_hadong CASCADE;
DROP SCHEMA IF EXISTS fdw_hoalac CASCADE;
DROP SERVER IF EXISTS hadong_server CASCADE;
DROP SERVER IF EXISTS hoalac_server CASCADE;

CREATE SCHEMA fdw_hadong;
CREATE SCHEMA fdw_hoalac;

CREATE SERVER hadong_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_hadong', dbname 'csdlpt_hadong', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER hadong_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

CREATE SERVER hoalac_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'postgres_hoalac', dbname 'csdlpt_hoalac', port '5432');

CREATE USER MAPPING FOR csdlpt_user
SERVER hoalac_server
OPTIONS (user 'csdlpt_user', password 'csdlpt_pass');

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER hadong_server
INTO fdw_hadong;

IMPORT FOREIGN SCHEMA public
LIMIT TO ("SinhVien", "GiangVien", "PhongHoc", "LopHocPhan", "LichHoc", "DangKy")
FROM SERVER hoalac_server
INTO fdw_hoalac;
