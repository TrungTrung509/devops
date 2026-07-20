# SCRIPTS - Hướng dẫn sử dụng các script vận hành

## Mục đích

Thư mục này chứa các script tự động hóa việc vận hành hệ thống Cơ sở dữ liệu phân tán.

## Danh sách Script

| Script | Mô tả |
|--------|--------|
| `reset_data.sh` | Xóa toàn bộ dữ liệu trên 3 site |
| `reseed.sh` | Sinh và import dữ liệu mẫu |
| `reindex_es.sh` | Khởi tạo và reindex Elasticsearch |
| `check_counts.sh` | Kiểm tra số bản ghi trên 3 site |
| `bootstrap_search.py` | Bootstrap Elasticsearch (Python) |
| `reindex_es.py` | Reindex dữ liệu vào ES (Python) |

## Yêu cầu

### Dependencies

```bash
# Python
pip install elasticsearch>=8.11.0 psycopg2-binary>=2.9.9

# Docker
docker --version
docker-compose --version
```

### Quyền thực thi

```bash
# Linux/Mac
chmod +x scripts/*.sh

# Windows (PowerShell)
# Scripts .sh cần chạy trong WSL hoặc Git Bash
```

## Cách sử dụng

### 1. Reset Data - Xóa dữ liệu

**Mục đích**: Xóa toàn bộ dữ liệu trên 3 site PostgreSQL và các service khác.

**Cú pháp**:
```bash
# Linux/Mac
./scripts/reset_data.sh

# Hoặc bash
bash scripts/reset_data.sh
```

**Script thực hiện**:
1. Truncate các bảng local (SinhVien, GiangVien, etc.)
2. FLUSHALL Redis
3. Xóa Elasticsearch index `hocphan`
4. Giữ nguyên replication subscriptions

**Cảnh báo**: Script yêu cầu xác nhận "yes" trước khi xóa.

---

### 2. Reseed - Sinh dữ liệu mẫu

**Mục đích**: Generate và import dữ liệu mẫu vào 3 site.

**Cú pháp**:
```bash
./scripts/reseed.sh
```

**Script thực hiện**:
1. Kiểm tra/tạo Python virtual environment
2. Chạy `generate_data.py` để sinh SQL files
3. Import common data vào 3 site
4. Import site data vào từng site
5. Import indexes

**Output**: Chạy `check_counts.sh` sau khi hoàn thành.

---

### 3. Reindex Elasticsearch - Đẩy dữ liệu vào ES

**Mục đích**: Bootstrap Elasticsearch và reindex dữ liệu từ PostgreSQL.

**Cú pháp**:
```bash
./scripts/reindex_es.sh

# Hoặc từng bước riêng:
python scripts/bootstrap_search.py --force
python scripts/reindex_es.py
```

**Script thực hiện**:
1. Bootstrap ES (tạo index template, xóa index cũ)
2. Reindex dữ liệu HocPhan từ PostgreSQL

---

### 4. Check Counts - Kiểm tra số bản ghi

**Mục đích**: Kiểm tra số bản ghi trên cả 3 site để xác nhận replication hoạt động đúng.

**Cú pháp**:
```bash
./scripts/check_counts.sh
```

**Output mẫu**:
```
━━━ BẢNG DÙNG CHUNG (Replication) ━━━

TABLE               HADONG     NGOCTRUC       HOALAC   MATCH?
────────────────────────────────────────────────────
CoSo                     3           3           3       ✓
Khoa                     4           4           4       ✓
HocPhan                 20          20          20       ✓
HocKy                    3           3           3       ✓

✓ Tất cả bảng dùng chung có số bản ghi KHỚP nhau!
```

---

## Các script Python

### bootstrap_search.py

Bootstrap Elasticsearch với index template.

```bash
# Chạy mặc định
python scripts/bootstrap_search.py

# Force recreate index
python scripts/bootstrap_search.py --force

# Chỉ verify
python scripts/bootstrap_search.py --verify-only

# Custom host
python scripts/bootstrap_search.py --host http://localhost:9200 --index hocphan
```

### reindex_es.py

Reindex dữ liệu từ PostgreSQL vào Elasticsearch.

```bash
# Chạy mặc định (đọc từ HADONG:5432)
python scripts/reindex_es.py

# Custom config
PG_HOST=localhost PG_PORT=5432 python scripts/reindex_es.py
```

## Kiểm tra trạng thái

### Kiểm tra Docker containers

```bash
docker-compose -f docker/docker-compose.yml ps
```

### Kiểm tra health

```bash
# PostgreSQL
docker exec -i csdlpt_hadong pg_isready -U csdlpt_user -d csdlpt_hadong

# Redis
docker exec -i csdlpt_redis redis-cli ping

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

### Kiểm tra replication

```bash
# Xem replication status
./scripts/check_counts.sh

# Hoặc SQL:
docker exec -i csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -c "SELECT * FROM pg_stat_replication;"
```

## Troubleshooting

### Lỗi: permission denied khi chạy .sh

```bash
# Thêm quyền thực thi
chmod +x scripts/*.sh
```

### Lỗi: Elasticsearch không kết nối được

```bash
# Kiểm tra container
docker logs csdlpt_elasticsearch

# Kiểm tra health
curl http://localhost:9200/_cluster/health
```

### Lỗi: PostgreSQL connection failed

```bash
# Kiểm tra container
docker ps | grep postgres

# Kiểm tra health
docker inspect --format='{{.State.Health.Status}}' csdlpt_hadong
```

### Lỗi: Python import error

```bash
# Cài đặt dependencies
pip install -r seeds/requirements.txt
```

## Thứ tự chạy đề xuất

```
1. Reset data (nếu cần reset)
   ./scripts/reset_data.sh

2. Reseed dữ liệu
   ./scripts/reseed.sh

3. Setup replication
   Get-Content sql/replication/01_setup_publisher.sql | docker exec -i csdlpt_hadong psql ...
   Get-Content sql/replication/02_setup_subscribers.sql | docker exec -i csdlpt_ngoctruc psql ...
   Get-Content sql/replication/02_setup_subscribers.sql | docker exec -i csdlpt_hoalac psql ...

4. Reindex Elasticsearch
   ./scripts/reindex_es.sh

5. Kiểm tra
   ./scripts/check_counts.sh
```

---

*Cập nhật: 2026-04-04*
