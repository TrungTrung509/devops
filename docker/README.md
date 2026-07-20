# DOCKER - Hướng dẫn sử dụng

## 1. Mục đích thư mục

Thư mục `docker/` chứa toàn bộ cấu hình container cho hệ thống Cơ sở dữ liệu phân tán, bao gồm:

- **docker-compose.yml**: Cấu hình Docker Compose cho 3 site + Redis + ES + Kibana
- **.env.example**: Template biến môi trường
- **healthcheck/**: Scripts kiểm tra health của các service

## 2. Giải thích từng service

| Service | Container | Port | Database | Mô tả |
|---------|-----------|------|----------|-------|
| `postgres_hadong` | csdlpt_hadong | 5432 | csdlpt_hadong | Site Hà Đông |
| `postgres_ngoctruc` | csdlpt_ngoctruc | 5433 | csdlpt_ngoctruc | Site Ngọc Trục |
| `postgres_hoalac` | csdlpt_hoalac | 5434 | csdlpt_hoalac | Site Hòa Lạc |
| `redis` | csdlpt_redis | 6379 | - | Cache layer |
| `elasticsearch` | csdlpt_elasticsearch | 9200 | - | Search engine |
| `kibana` | csdlpt_kibana | 5601 | - | Dashboard |

## 3. Cách sử dụng

### 3.1 Copy .env.example thành .env

```bash
cd docker
cp .env.example .env
```

### 3.2 Chỉnh sửa .env (nếu cần)

Mở file `.env` và chỉnh các giá trị cho phù hợp với máy của bạn.

### 3.3 Khởi động toàn bộ hệ thống

```bash
cd docker
docker-compose up -d
```

### 3.4 Khởi động từng service cụ thể

```bash
# Chỉ PostgreSQL
docker-compose up -d postgres_hadong postgres_ngoctruc postgres_hoalac

# Chỉ Redis
docker-compose up -d redis

# Chỉ Elasticsearch + Kibana
docker-compose up -d elasticsearch kibana
```

## 4. Cách kiểm tra container healthy

### 4.1 Kiểm tra trạng thái container

```bash
docker-compose ps
```

### 4.2 Kiểm tra health status chi tiết

```bash
docker inspect --format='{{.State.Health.Status}}' csdlpt_hadong
docker inspect --format='{{.State.Health.Status}}' csdlpt_ngoctruc
docker inspect --format='{{.State.Health.Status}}' csdlpt_hoalac
docker inspect --format='{{.State.Health.Status}}' csdlpt_redis
docker inspect --format='{{.State.Health.Status}}' csdlpt_elasticsearch
```

### 4.3 Kiểm tra kết nối PostgreSQL

```bash
# Kiểm tra từ container
docker exec -it csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT 1;"

# Kiểm tra từ máy host
psql -h localhost -p 5432 -U csdlpt_user -d csdlpt_hadong -c "SELECT 1;"
```

### 4.4 Kiểm tra kết nối Redis

```bash
docker exec -it csdlpt_redis redis-cli ping
```

### 4.5 Kiểm tra Elasticsearch

```bash
curl http://localhost:9200
```

### 4.6 Kiểm tra Kibana

```bash
curl http://localhost:5601/api/status
```

## 5. Cách stop / restart / remove

### 5.1 Dừng tất cả container

```bash
docker-compose down
```

### 5.2 Dừng và xóa volumes (reset hoàn toàn)

```bash
docker-compose down -v
```

### 5.3 Restart một service cụ thể

```bash
docker-compose restart postgres_hadong
```

### 5.4 Xem logs

```bash
# Logs tất cả
docker-compose logs -f

# Logs một service
docker-compose logs -f postgres_hadong

# Logs 20 dòng gần nhất
docker-compose logs --tail=20 postgres_hadong
```

## 6. Các lỗi thường gặp

### 6.1 Port đã được sử dụng

```
Error: port is already allocated
```

**Giải pháp**: Kiểm tra port đang dùng và đổi port trong `.env`

```bash
# Kiểm tra port
netstat -an | grep 5432

# Đổi port trong .env
HADONG_PORT=5435
```

### 6.2 Không đủ RAM cho Elasticsearch

```
Bootstrap check failed
```

**Giải pháp**: Giảm bộ nhớ Elasticsearch trong docker-compose.yml

```yaml
environment:
  - "ES_JAVA_OPTS=-Xms256m -Xmx256m"
```

### 6.3 Volume permission denied

```
Permission denied: '/var/lib/postgresql/data'
```

**Giải pháp**: Xóa volume cũ và tạo lại

```bash
docker-compose down -v
docker volume rm csdlpt_postgres_hadong_data
docker-compose up -d
```

### 6.4 Container không start được

```bash
# Xem logs chi tiết
docker-compose logs postgres_hadong

# Rebuild container
docker-compose up -d --force-recreate postgres_hadong
```

## 7. Thứ tự khởi động

Hệ thống được cấu hình `depends_on` với `condition: service_healthy`:

1. **PostgreSQL sites** - Khởi động trước, cần healthy trước khi các service khác start
2. **Elasticsearch** - Khởi động sau PostgreSQL
3. **Kibana** - Khởi động cuối cùng, phụ thuộc Elasticsearch healthy

## 8. Mapping Site - Cơ sở

| Site | Container | Cơ sở quản lý | Mã Cơ sở |
|------|-----------|---------------|-----------|
| site_hadong | csdlpt_hadong | Hà Đông | HADONG |
| site_ngoctruc | csdlpt_ngoctruc | Ngọc Trục | NGOCTRUC |
| site_hoalac | csdlpt_hoalac | Hòa Lạc | HOALAC |

## 9. Khởi tạo database tự động

Khi container PostgreSQL khởi động lần đầu, Docker sẽ tự động chạy các script SQL theo thứ tự:

1. `/docker-entrypoint-initdb.d/00_common/` - Bảng dùng chung (CoSo, Khoa, HocPhan, HocKy)
2. `/docker-entrypoint-initdb.d/01_site/` - Bảng cục bộ (SinhVien, GiangVien, PhongHoc, LopHocPhan, LichHoc, DangKy)

---

*Lưu ý: Chỉ chạy init script khi tạo database lần đầu. Muốn chạy lại, phải xóa volume.*
