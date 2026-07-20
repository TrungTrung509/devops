# Distributed views

Thu muc nay chua cac view tong hop tren moi site sau khi FDW da duoc cau hinh.

- `01_hadong_distributed_views.sql`: view tong hop cho HADONG
- `02_ngoctruc_distributed_views.sql`: view tong hop cho NGOCTRUC
- `03_hoalac_distributed_views.sql`: view tong hop cho HOALAC

Moi site tao cac view sau:

- `vw_sinhvien_toantruong`
- `vw_giangvien_toantruong`
- `vw_phonghoc_toantruong`
- `vw_lophocphan_toantruong`
- `vw_lichhoc_toantruong`
- `vw_dangky_toantruong`

Kiem tra nhanh tai HADONG:

```powershell
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\dv"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_sinhvien_toantruong;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_lophocphan_toantruong;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_dangky_toantruong;"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM vw_sinhvien_toantruong LIMIT 5;"
```

SQL thuần de copy vao psql/pgAdmin:

```sql
SELECT table_schema, table_name
FROM information_schema.views
WHERE table_name LIKE 'vw\\_%\\_toantruong' ESCAPE '\'
ORDER BY table_schema, table_name;

SELECT COUNT(*) FROM vw_sinhvien_toantruong;
SELECT COUNT(*) FROM vw_lophocphan_toantruong;
SELECT COUNT(*) FROM vw_dangky_toantruong;

SELECT * FROM vw_sinhvien_toantruong LIMIT 5;
SELECT * FROM vw_dangky_toantruong LIMIT 5;
```
