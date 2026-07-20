#!/usr/bin/env python3
"""
Reindex Elasticsearch - Đẩy dữ liệu từ PostgreSQL vào Elasticsearch
Cho hệ thống Cơ sở dữ liệu phân tán - Đăng ký học phần

Script này:
1. Kết nối PostgreSQL (site HADONG)
2. Đọc dữ liệu HocPhan, Khoa
3. Build nested documents
4. Bulk index vào Elasticsearch
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    import psycopg2
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
except ImportError as e:
    print(f"ERROR: Thiếu thư viện - {e}")
    print("Cài đặt: pip install psycopg2-binary elasticsearch>=8.11.0")
    sys.exit(1)

# CẤU HÌNH
# PostgreSQL (site HADONG)
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))
PG_DB = os.environ.get("PG_DB", "csdlpt_hadong")
PG_USER = os.environ.get("PG_USER", "csdlpt_user")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "csdlpt_pass")

# Elasticsearch
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_INDEX = os.environ.get("ES_INDEX", "hocphan")
ES_TIMEOUT = 30

# Màu sắc
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {msg}")


def get_db_connection():
    """Kết nối PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        log_success(f"Kết nối PostgreSQL thành công ({PG_HOST}:{PG_PORT}/{PG_DB})")
        return conn
    except Exception as e:
        log_error(f"Không thể kết nối PostgreSQL: {e}")
        sys.exit(1)


def fetch_hocphan_data(conn) -> List[Dict[str, Any]]:
    """Lấy dữ liệu HocPhan từ PostgreSQL"""
    query = """
        SELECT
            hp."MaHP",
            hp."TenHP",
            hp."SoTinChi",
            hp."SoTietLyThuyet",
            hp."SoTietThucHanh",
            hp."LoaiHocPhan",
            hp."MaKhoa",
            hp."MoTa",
            hp."TrangThai",
            hp."NgayTao",
            k."TenKhoa"
        FROM "HocPhan" hp
        LEFT JOIN "Khoa" k ON hp."MaKhoa" = k."MaKhoa"
        ORDER BY hp."MaHP"
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            log_info(f"Đã lấy {len(rows)} học phần từ PostgreSQL")

            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error(f"Lỗi khi lấy dữ liệu HocPhan: {e}")
        sys.exit(1)


# (fetch_tienquyet_data removed since TienQuyet is no longer used)


def build_documents(hocphan_data: List[Dict]) -> List[Dict]:
    """Build documents cho Elasticsearch"""
    documents = []

    # Debug: print first row columns
    if hocphan_data:
        print(f"[DEBUG] First row keys: {list(hocphan_data[0].keys())}")

    for hp in hocphan_data:
        # Normalize keys to lowercase
        hp_lower = {k.lower(): v for k, v in hp.items()}
        mahp = hp_lower["mahp"]

        # Map field names (handle both naming conventions)
        sotiet_thuchanh = hp_lower.get("sotietteuchanh") or hp_lower.get("sotietthuchanh") or 0

        # Format NgayTao: handle both date and datetime with microseconds
        ngaytao_val = hp_lower.get("ngaytao")
        if ngaytao_val:
            if hasattr(ngaytao_val, 'strftime'):
                formatted_ngaytao = ngaytao_val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                val_str = str(ngaytao_val)[:19]
                if 'T' in val_str:
                    val_str = val_str.replace('T', ' ')
                formatted_ngaytao = val_str
        else:
            formatted_ngaytao = None

        doc = {
            "MaHP": mahp,
            "TenHP": hp_lower["tenhp"],
            "SoTinChi": hp_lower["sotinchi"],
            "SoTietLyThuyet": hp_lower["sotietlythuyet"],
            "SoTietThucHanh": sotiet_thuchanh,
            "LoaiHocPhan": hp_lower["loaihocphan"],
            "MaKhoa": hp_lower["makhoa"],
            "TenKhoa": hp_lower["tenkhoa"],
            "MoTa": hp_lower["mota"],
            "TrangThai": hp_lower["trangthai"],
            "NgayTao": formatted_ngaytao,
            "suggest": {
                "input": [mahp, hp_lower["tenhp"]],
                "weight": 1
            }
        }

        # Tạo search_text cho full-text search
        search_parts = [mahp, hp_lower["tenhp"]]
        if hp_lower["tenkhoa"]:
            search_parts.append(hp_lower["tenkhoa"])
        doc["search_text"] = " ".join(filter(None, search_parts))

        documents.append(doc)

    return documents


def generate_actions(documents: List[Dict], index_name: str):
    """Generate actions cho bulk indexing"""
    for doc in documents:
        yield {
            "_index": index_name,
            "_id": doc["MaHP"],
            "_source": doc
        }


def bulk_index(es: Elasticsearch, documents: List[Dict], index_name: str) -> bool:
    """Bulk index documents vào Elasticsearch"""
    try:
        # Create index with proper mappings
        index_settings = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "vietnamese_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    },
                    "normalizer": {
                        "lowercase_normalizer": {
                            "type": "custom",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "MaHP": {"type": "keyword", "copy_to": "search_text"},
                    "TenHP": {
                        "type": "text",
                        "analyzer": "vietnamese_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "SoTinChi": {"type": "integer"},
                    "SoTietLyThuyet": {"type": "integer"},
                    "SoTietThucHanh": {"type": "integer"},
                    "LoaiHocPhan": {"type": "keyword"},
                    "MaKhoa": {"type": "keyword", "copy_to": "search_text"},
                    "TenKhoa": {"type": "text", "analyzer": "vietnamese_analyzer"},
                    "MoTa": {"type": "text", "analyzer": "vietnamese_analyzer"},
                    "TrangThai": {"type": "keyword"},
                    "NgayTao": {"type": "date"},
                    "search_text": {"type": "text", "analyzer": "vietnamese_analyzer"},
                    "suggest": {"type": "completion", "analyzer": "simple"}
                }
            }
        }

        try:
            es.indices.create(index=index_name, **index_settings)
            log_info(f"Đã tạo index mới: {index_name}")
        except Exception as e:
            # Nếu index đã tồn tại thì bỏ qua lỗi, hoặc báo log
            if "resource_already_exists_exception" in str(e):
                log_info(f"Index '{index_name}' đã tồn tại, tiếp tục cập nhật dữ liệu.")
            else:
                log_warning(f"Lưu ý khi tạo index: {e}")

        success, failed = bulk(
            es,
            generate_actions(documents, index_name),
            raise_on_error=False,
            raise_on_exception=False,
            stats_only=False
        )

        if failed:
            log_warning(f"Có {len(failed)} document bị lỗi khi index")
            for error in failed[:5]:  # In 5 lỗi đầu
                log_error(f"  - {error}")
            return False

        log_success(f"Đã index {success} document thành công")
        return True

    except Exception as e:
        log_error(f"Lỗi khi bulk index: {e}")
        return False


def main():
    print()
    print(Colors.HEADER + Colors.BOLD + "=" * 60)
    print("  REINDEX ELASTICSEARCH SCRIPT")
    print("  Đẩy dữ liệu PostgreSQL vào Elasticsearch")
    print("=" * 60 + Colors.ENDC)
    print()

    # Kết nối PostgreSQL
    print()
    log_info("Kết nối PostgreSQL...")
    conn = get_db_connection()

    # Kết nối Elasticsearch
    print()
    log_info(f"Kết nối Elasticsearch tại {ES_HOST}...")
    try:
        es = Elasticsearch(
            [ES_HOST],
            request_timeout=ES_TIMEOUT,
            retry_on_timeout=True,
            max_retries=3
        )

        if not es.ping():
            log_error("Không thể kết nối Elasticsearch!")
            sys.exit(1)

        log_success("Đã kết nối Elasticsearch")

    except Exception as e:
        log_error(f"Lỗi kết nối Elasticsearch: {e}")
        sys.exit(1)

    # Lấy dữ liệu từ PostgreSQL
    print()
    log_info("Lấy dữ liệu từ PostgreSQL...")
    hocphan_data = fetch_hocphan_data(conn)

    # Build documents
    print()
    log_info("Build documents...")
    documents = build_documents(hocphan_data)
    log_info(f"Đã build {len(documents)} documents")

    # Bulk index
    print()
    log_info(f"Indexing vào Elasticsearch (index: {ES_INDEX})...")
    if bulk_index(es, documents, ES_INDEX):
        print()
        log_success("=" * 60)
        log_success("REINDEX HOÀN TẤT!")
        log_success("=" * 60)
    else:
        print()
        log_warning("Reindex hoàn thành với một số lỗi")

    # Cleanup
    conn.close()
    print()
    log_info("Đã đóng kết nối")


if __name__ == "__main__":
    main()
