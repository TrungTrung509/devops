# DATABASE TẬP TRUNG (CENTRALIZED)

## Mục đích

Thư mục này chứa schema và script để tạo database tập trung `csdlpt_centralized` dùng cho việc so sánh hiệu năng với mô hình phân tán.

## Các file

- `01_centralized_schema.sql` - Schema tập trung
- `02_import_data.sql` - Script import dữ liệu từ 3 site

## Database Info

- **Database**: csdlpt_centralized
- **Port**: 5435
- **User**: csdlpt_user
- **Password**: csdlpt_pass
- **Container**: csdlpt_centralized

## Cách chạy

```powershell
# 1. Bật container
docker compose -f docker/docker-compose.yml up -d postgres_centralized

# 2. Setup schema và import dữ liệu
powershell -ExecutionPolicy Bypass -File scripts/setup_centralized_db.ps1

# 3. Kiểm tra dữ liệu
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -c "SELECT COUNT(*) FROM \"SinhVien\";"
```

## Schema

Database tập trung gồm:

- **Common tables** (nhân bản từ HADONG):
  - CoSo, users, Khoa, HocPhan, HocKy

- **Local tables** (gom từ 3 site):
  - SinhVien, GiangVien, PhongHoc, LopHocPhan, LichHoc, DangKy

- **Audit tables**:
  - DangKy_3PC, DangKy_ChuyenCoSo, NhatKyPhucHoi, NhatKyThaoTac
  - ReplicationOutbox, SiteStatus

## Import dữ liệu

Dữ liệu được import từ 3 site qua dblink:
- HADONG (port 5432)
- NGOCTRUC (port 5433)  
- HOALAC (port 5434)

Common tables chỉ import 1 lần từ HADONG.
Local tables import từ cả 3 site, thêm cột `SourceSite` để truy vết.
