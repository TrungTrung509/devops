# SQL - Scripts Database

## Muc dich

Thu muc `sql/` chua cac script SQL bo sung sau khi da tao schema.

## Cac nhom file

| File | Mo ta | Phu trach |
|------|-------|-----------|
| `indexes.sql` | Indexes cho cac bang | Viet |
| `procedures/*.sql` | Stored procedures | Tuan |
| `views/*.sql` | View tong hop toan truong | Tuan |
| `fdw/*.sql` | Cau hinh `postgres_fdw` | Tuan |
| `queries/*.sql` | Truy van phan tan | Tuan |
| `replication/*.sql` | Cau hinh replication | Viet |

## Indexes

Chay `sql/indexes.sql` tren tat ca site:

```powershell
Get-Content sql/indexes.sql | docker exec -i csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong
Get-Content sql/indexes.sql | docker exec -i csdlpt_ngoctruc psql -U csdlpt_user -d csdlpt_ngoctruc
Get-Content sql/indexes.sql | docker exec -i csdlpt_hoalac psql -U csdlpt_user -d csdlpt_hoalac
```

Kiem tra indexes:

```sql
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public';

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'DangKy';
```

## Cac thu muc con

### `sql/procedures/`

Stored procedures cho nghiep vu dang ky, huy hoc phan.

### `sql/views/`

View tong hop du lieu tu nhieu site qua FDW.

### `sql/fdw/`

Script cau hinh `postgres_fdw` de truy van lien site.

### `sql/queries/`

Truy van phan tan theo yeu cau do an.

Hien tai da co:

- `sql/queries/01_distributed_reports.sql`: 5 truy van phan tan cho thong ke dang ky hoc phan

### `sql/replication/`

Script cau hinh logical replication cho bang dung chung.

## Test View va FDW

Sau khi chay:

```powershell
docker compose -f docker\docker-compose.yml up -d
powershell -ExecutionPolicy Bypass -File .\infra\scripts\seed.ps1
```

co the kiem tra nhanh phan FDW va view bang cac lenh sau.

### 1. Kiem tra bootstrap FDW

```powershell
docker logs csdlpt_fdw_setup
```

Ky vong co dong:

```text
FDW bootstrap completed.
```

### 2. Kiem tra schema FDW, foreign table, view

```powershell
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\dn"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\det+"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\dv"
```

Ky vong thay:

- schema `fdw_ngoctruc`, `fdw_hoalac`
- foreign table trong `fdw_*`
- cac view `vw_*_toantruong`

### 3. Kiem tra query FDW truc tiep

```powershell
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) AS sv_ngoctruc FROM fdw_ngoctruc.sinhvien;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) AS sv_hoalac FROM fdw_hoalac.sinhvien;"
```

### 4. Kiem tra view tong hop

```powershell
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) AS sv_toantruong FROM vw_sinhvien_toantruong;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) AS lhp_toantruong FROM vw_lophocphan_toantruong;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) AS dk_toantruong FROM vw_dangky_toantruong;"
```

Neu da seed theo README goc, co the ky vong gan dung:

- `vw_sinhvien_toantruong`: 360 dong
- `vw_lophocphan_toantruong`: 75 dong

### 5. Xem mau du lieu

```powershell
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM vw_sinhvien_toantruong LIMIT 5;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM vw_dangky_toantruong LIMIT 5;"
```

### 6. Cac cau lenh SQL de copy truc tiep vao PostgreSQL

Ket noi vao mot site, vi du `csdlpt_hadong`, roi chay:

```sql
-- Xem schema FDW da duoc tao chua
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('fdw_ngoctruc', 'fdw_hoalac')
ORDER BY schema_name;

-- Xem foreign table da duoc import chua
SELECT foreign_table_schema, foreign_table_name
FROM information_schema.foreign_tables
ORDER BY foreign_table_schema, foreign_table_name;

-- Xem cac view tong hop
SELECT table_schema, table_name
FROM information_schema.views
WHERE table_name LIKE 'vw\\_%\\_toantruong' ESCAPE '\'
ORDER BY table_schema, table_name;

-- Test query FDW truc tiep
SELECT COUNT(*) AS sv_ngoctruc FROM fdw_ngoctruc.sinhvien;
SELECT COUNT(*) AS sv_hoalac FROM fdw_hoalac.sinhvien;

-- Test cac view tong hop
SELECT COUNT(*) AS sv_toantruong FROM vw_sinhvien_toantruong;
SELECT COUNT(*) AS gv_toantruong FROM vw_giangvien_toantruong;
SELECT COUNT(*) AS phong_toantruong FROM vw_phonghoc_toantruong;
SELECT COUNT(*) AS lhp_toantruong FROM vw_lophocphan_toantruong;
SELECT COUNT(*) AS lich_toantruong FROM vw_lichhoc_toantruong;
SELECT COUNT(*) AS dk_toantruong FROM vw_dangky_toantruong;

-- Xem du lieu mau
SELECT * FROM vw_sinhvien_toantruong LIMIT 5;
SELECT * FROM vw_lophocphan_toantruong LIMIT 5;
SELECT * FROM vw_dangky_toantruong LIMIT 5;

-- Vi du thong ke phan tan tu view
SELECT MaCoSo, COUNT(*) AS SoLuongSinhVien
FROM vw_sinhvien_toantruong
GROUP BY MaCoSo
ORDER BY MaCoSo;

SELECT MaCoSo, COUNT(*) AS SoLopMo
FROM vw_lophocphan_toantruong
GROUP BY MaCoSo
ORDER BY MaCoSo;

SELECT TrangThaiDangKy, COUNT(*) AS SoLuong
FROM vw_dangky_toantruong
GROUP BY TrangThaiDangKy
ORDER BY TrangThaiDangKy;
```

## Ghi chu

- View chi luu cau lenh `SELECT`, khong luu du lieu rieng.
- Moi lan query view, PostgreSQL se lay du lieu moi nhat tu bang local va foreign table.
- Neu dung `docker compose down -v`, database se bi tao lai va FDW/view se duoc bootstrap lai.
