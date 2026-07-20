# Benchmark: Centralized vs Distributed Database

## Mục đích

Benchmark so sánh hiệu năng giữa:
- **Mô hình tập trung**: 1 PostgreSQL duy nhất (`csdlpt_centralized`, port 5435)
- **Mô hình phân tán**: 3 PostgreSQL site + FDW (`csdlpt_hadong`, `csdlpt_ngoctruc`, `csdlpt_hoalac`)

## Các file

| File | Mô tả |
|------|--------|
| `centralized_vs_distributed.sql` | Tài liệu mô tả các cặp query benchmark |
| `centralized_queries.sql` | 7 query cho mô hình tập trung |
| `distributed_queries.sql` | 7 query cho mô hình phân tán |

## Các cặp query benchmark

| # | Tên | Loại query | Mục tiêu |
|---|------|------------|------------|
| 1 | `Q1_LOCAL_LOPHP` | LOCAL | Lấy danh sách lớp HP theo cơ sở |
| 2 | `Q2_SV_THEO_COSO` | GLOBAL | Thống kê SV theo cơ sở |
| 3 | `Q3_TY_LE_LOPDAY` | GLOBAL | Tỷ lệ lấp đầy lớp HP toàn trường |
| 4 | `Q4_DK_CHEO_COSO` | GLOBAL | SV đăng ký chéo cơ sở |
| 5 | `Q5_TOP_HP_NHIU_SV` | GLOBAL | Học phần nhiều SV nhất |
| 6 | `Q6_KIEM_TRA_SISO` | LOCAL | Kiểm tra sĩ số lớp |
| 7 | `Q7_TONG_HOP_HOCKY` | GLOBAL | Tổng hợp học kỳ |

## Cách chạy benchmark

### Chạy trên centralized (HADONG site)
```bash
docker exec -i csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -f centralized_queries.sql
```

### Chạy trên distributed (HADONG site)
```bash
docker exec -i csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -f distributed_queries.sql
```

## Cách đọc kết quả

Mỗi query có:
- `Planning Time`: Thời gian lập kế hoạch
- `Execution Time`: Thời gian thực thi
- `Buffers`: Số buffer đọc/ghi
- `Foreign Scan`: Có dùng FDW scan không (chỉ có trong distributed)

## Kỳ vọng kết quả

| Loại query | Centralized | Distributed |
|-----------|-------------|-------------|
| LOCAL | Chậm hơn một chút (dữ liệu trong 1 DB lớn) | Nhanh hơn (FDW view nhỏ) |
| GLOBAL | Nhanh hơn (không cần FDW) | Chậm hơn (FDW overhead) |

Lưu ý: Với dataset nhỏ (hàng chục-bàng trăm dòng), chênh lệch thời gian có thể không đáng kể. Xu hướng kiến trúc vẫn đúng.
