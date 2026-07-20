# FDW setup

Thu muc nay chua cau hinh `postgres_fdw` cho ca 3 site.

- `01_hadong_fdw.sql`: HADONG ket noi NGOCTRUC va HOALAC
- `02_ngoctruc_fdw.sql`: NGOCTRUC ket noi HADONG va HOALAC
- `03_hoalac_fdw.sql`: HOALAC ket noi HADONG va NGOCTRUC

Moi script se:

1. Bat `postgres_fdw`
2. Tao schema `fdw_*` cho site tu xa
3. Tao `SERVER` va `USER MAPPING`
4. `IMPORT FOREIGN SCHEMA` cho cac bang local can truy van lien site:
   - `sinhvien`
   - `giangvien`
   - `phonghoc`
   - `lophocphan`
   - `lichhoc`
   - `dangky`

Luu y:

- Khong mount truc tiep cac file nay vao `docker-entrypoint-initdb.d/`
- Repo dung container bootstrap `csdlpt_fdw_setup` de chay sau khi ca 3 PostgreSQL healthy


<!-- Check FDW -->

# 1. Kiểm tra FDW schema và server trên Hadong
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\dn"
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\des"

# 2. Kiểm tra foreign tables đã import
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM information_schema.foreign_tables;"

# 3. Kiểm tra số lượng sinh viên từng site
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM \"SinhVien\";"                    # Local
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM fdw_ngoctruc.\"SinhVien\";"      # Ngọc Trục
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM fdw_hoalac.\"SinhVien\";"        # Hòa Lạc

# 4. Kiểm tra view tổng hợp toàn trường
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_sinhvien_toantruong;"

# 5. Kiểm tra giảng viên
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_giangvien_toantruong;"

# 6. Kiểm tra lớp học phần
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT COUNT(*) FROM vw_lophocphan_toantruong;"

# 7. Xem chi tiết dữ liệu sinh viên từ các site
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM fdw_ngoctruc.\"SinhVien\" LIMIT 5;"

# 8. Kiểm tra tất cả views
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "\dv"