# SEARCH - Elasticsearch Configuration

## Mục đích

Thư mục này chứa cấu hình Elasticsearch cho hệ thống CSDL phân tán.

## Cấu trúc

```
search/
├── index_templates/          # Index template JSON files
│   └── hocphan_template.json # Template cho HocPhan index
└── README.md                 # Tài liệu này
```

## Index Templates

### hocphan_template.json

Template cho index `hocphan`, hỗ trợ:

- **Full-text search tiếng Việt**: Sử dụng Vietnamese analyzer
- **Completion suggester**: Cho autocomplete
- **Keyword fields**: Cho exact match (MaHP, MaKhoa)

## Cấu trúc Document

```json
{
  "MaHP": "CS1001",
  "TenHP": "Nhập môn lập trình",
  "SoTinChi": 3,
  "SoTietLyThuyet": 30,
  "SoTietThucHanh": 30,
  "LoaiHocPhan": "BatBuoc",
  "MaKhoa": "CNTT",
  "TenKhoa": "Công nghệ thông tin",
  "MoTa": "Môn học cơ bản...",
  "TrangThai": "HoatDong",
  "NgayTao": "2026-01-15",
  "search_text": "CS1001 Nhập môn lập trình Công nghệ thông tin",
  "suggest": {
    "input": ["CS1001", "Nhập môn lập trình"]
  }
}
```

## Sử dụng

### Bootstrap Elasticsearch

```bash
# Chạy script bootstrap
python scripts/bootstrap_search.py --force

# Verify
python scripts/bootstrap_search.py --verify-only
```

### Reindex dữ liệu

```bash
# Chạy reindex
python scripts/reindex_es.py

# Hoặc dùng shell script
./scripts/reindex_es.sh
```

### Kiểm tra Index

```bash
# Xem mapping
curl http://localhost:9200/hocphan/_mapping?pretty

# Xem settings
curl http://localhost:9200/hocphan/_settings?pretty

# Đếm documents
curl http://localhost:9200/hocphan/_count

# Search test
curl -X POST "http://localhost:9200/hocphan/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "TenHP": "nhập môn"
    }
  }
}
'
```

## Vietnamese Search

Template sử dụng `vietnamese_analyzer` để hỗ trợ search tiếng Việt:

```json
{
  "analyzer": {
    "vietnamese_analyzer": {
      "type": "custom",
      "tokenizer": "standard",
      "filter": ["lowercase", "asciifolding", "vietnamese_tokenizer"]
    }
  }
}
```

### Ví dụ search

```bash
# Search theo tên (hỗ trợ tiếng Việt)
curl -X POST "http://localhost:9200/hocphan/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "TenHP": {
        "query": "lap trinh",
        "analyzer": "vietnamese_analyzer"
      }
    }
  }
}
'

# Autocomplete / Suggester
curl -X POST "http://localhost:9200/hocphan/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "suggest": {
    "course-suggest": {
      "prefix": "nha",
      "completion": {
        "field": "TenHP.suggest",
        "size": 5
      }
    }
  }
}
'

# Filter theo khoa
curl -X POST "http://localhost:9200/hocphan/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"TenHP": "môn"}}
      ],
      "filter": [
        {"term": {"MaKhoa": "CNTT"}}
      ]
    }
  }
}
'
```

## API Endpoints

### Elasticsearch

| Endpoint | Mô tả |
|----------|--------|
| `GET /_cluster/health` | Cluster health |
| `GET /hocphan/_count` | Document count |
| `GET /hocphan/_mapping` | Index mapping |
| `POST /hocphan/_search` | Search |

### Kibana

| Endpoint | Mô tả |
|----------|--------|
| `GET /5601/api/status` | Kibana status |
| `GET /5601/api/health` | Kibana health |

## Xóa và tạo lại Index

```bash
# Xóa index
curl -X DELETE "http://localhost:9200/hocphan"

# Tạo lại và reindex
./scripts/reindex_es.sh
```

---

*Cập nhật: 2026-04-04*
