#!/usr/bin/env python3
"""
Bootstrap Elasticsearch - Khởi tạo Elasticsearch Index và Template
Cho hệ thống Cơ sở dữ liệu phân tán - Đăng ký học phần

Script này:
1. Chờ Elasticsearch healthy
2. Xóa index cũ (nếu có)
3. Push index template
4. Tạo index mới
5. Kiểm tra cấu hình
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import NotFoundError, ConnectionError
except ImportError:
    print("ERROR: Chưa cài đặt thư viện elasticsearch")
    print("Cài đặt: pip install elasticsearch>=8.11.0")
    sys.exit(1)

# CẤU HÌNH
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_TIMEOUT = 30  # seconds
ES_INDEX_NAME = "hocphan"
ES_TEMPLATE_FILE = Path(__file__).parent.parent / "search" / "index_templates" / "hocphan_template.json"
args = None

# Màu sắc cho terminal
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


def wait_for_elasticsearch(es: Elasticsearch, max_retries: int = 30, delay: int = 5) -> bool:
    """Chờ Elasticsearch trở nên healthy"""
    log_info(f"Đang chờ Elasticsearch tại {ES_HOST}...")

    for attempt in range(1, max_retries + 1):
        try:
            # Kiểm tra cluster health
            health = es.cluster.health(timeout="5s")
            status = health.get("status", "unknown")

            if status in ["green", "yellow"]:
                log_success(f"Elasticsearch cluster status: {status}")
                return True

            log_warning(f"Lần thử {attempt}/{max_retries}: Cluster status = {status}")

        except ConnectionError as e:
            log_warning(f"Lần thử {attempt}/{max_retries}: Không kết nối được - {e}")

        if attempt < max_retries:
            time.sleep(delay)

    log_error(f"Không thể kết nối Elasticsearch sau {max_retries} lần thử")
    return False


def check_and_create_index(es: Elasticsearch, index_name: str, template_path: Path, args=None) -> bool:
    """Tạo index mới nếu chưa có"""
    try:
        # Kiểm tra index đã tồn tại
        if es.indices.exists(index=index_name):
            log_warning(f"Index '{index_name}' đã tồn tại")

            if args and args.force:
                log_info(f"Force mode: Xóa index cũ...")
                es.indices.delete(index=index_name)
                log_success(f"Đã xóa index '{index_name}'")
            else:
                response = input(f"Bạn có muốn xóa và tạo lại? (y/N): ")
                if response.lower() == 'y':
                    es.indices.delete(index=index_name)
                    log_success(f"Đã xóa index '{index_name}'")
                else:
                    log_info("Giữ nguyên index cũ")
                    return True

        # Tạo index mới với settings từ template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        # Tạo index với settings và mappings từ template
        index_body = {
            "settings": template_data["template"]["settings"],
            "mappings": template_data["template"]["mappings"],
            "aliases": template_data["template"].get("aliases", {})
        }

        es.indices.create(index=index_name, body=index_body)
        log_success(f"Đã tạo index '{index_name}'")
        return True

    except Exception as e:
        log_error(f"Lỗi khi tạo index: {e}")
        return False


def push_template(es: Elasticsearch, template_name: str, template_path: Path) -> bool:
    """Push index template lên Elasticsearch"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        # Xóa template cũ nếu tồn tại
        try:
            es.indices.delete_index_template(name=template_name)
            log_warning(f"Đã xóa template cũ '{template_name}'")
        except NotFoundError:
            pass

        # Tạo index template mới
        es.indices.put_index_template(
            name=template_name,
            body=template_data
        )

        log_success(f"Đã push template '{template_name}'")
        return True

    except Exception as e:
        log_error(f"Lỗi khi push template: {e}")
        return False


def verify_setup(es: Elasticsearch, index_name: str) -> bool:
    """Kiểm tra cấu hình Elasticsearch"""
    log_info("Đang kiểm tra cấu hình...")

    try:
        # 1. Kiểm tra index
        if not es.indices.exists(index=index_name):
            log_error(f"Index '{index_name}' không tồn tại!")
            return False
        log_success(f"Index '{index_name}' tồn tại")

        # 2. Kiểm tra cluster health
        health = es.cluster.health(index=index_name)
        log_info(f"  - Cluster status: {health.get('status')}")
        log_info(f"  - Number of shards: {health.get('number_of_shards')}")
        log_info(f"  - Number of replicas: {health.get('number_of_replicas')}")

        # 3. Kiểm tra mappings
        mappings = es.indices.get_mapping(index=index_name)
        if mappings and index_name in mappings:
            properties = mappings[index_name].get("mappings", {}).get("properties", {})
            log_info(f"  - Fields mapped: {len(properties)}")

        # 4. Test search
        result = es.search(index=index_name, body={"query": {"match_all": {}}, "size": 0})
        log_info(f"  - Documents: {result['hits']['total']['value']}")

        log_success("Cấu hình Elasticsearch hợp lệ!")
        return True

    except Exception as e:
        log_error(f"Lỗi khi kiểm tra: {e}")
        return False


def list_elasticsearch_info(es: Elasticsearch):
    """Liệt kê thông tin Elasticsearch"""
    log_info("=" * 50)
    log_info("THÔNG TIN ELASTICSEARCH")
    log_info("=" * 50)

    # Cluster info
    info = es.info()
    log_info(f"Cluster name: {info.get('cluster_name')}")
    log_info(f"Cluster UUID: {info.get('cluster_uuid')}")
    log_info(f"Version: {info.get('version', {}).get('number')}")

    # Indices
    indices = es.cat.indices(format="json")
    log_info(f"\nTotal indices: {len(indices)}")

    for idx in indices:
        name = idx.get("index", "unknown")
        docs = idx.get("docs.count", "0")
        size = idx.get("store.size", "0")
        health = idx.get("health", "-")
        log_info(f"  - {name}: {docs} docs, {size} ({health})")

    log_info("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap Elasticsearch cho hệ thống CSDL Phân tán"
    )
    parser.add_argument(
        "--host",
        default=ES_HOST,
        help=f"Elasticsearch host (default: {ES_HOST})"
    )
    parser.add_argument(
        "--index",
        default=ES_INDEX_NAME,
        help=f"Index name (default: {ES_INDEX_NAME})"
    )
    parser.add_argument(
        "--template",
        default=str(ES_TEMPLATE_FILE),
        help=f"Template file path (default: {ES_TEMPLATE_FILE})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate index (xóa index cũ)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Không chờ Elasticsearch healthy"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Chỉ kiểm tra, không tạo gì"
    )

    global args
    args = parser.parse_args()

    print()
    print(Colors.HEADER + Colors.BOLD + "=" * 60)
    print("  ELASTICSEARCH BOOTSTRAP SCRIPT")
    print("  Hệ thống Cơ sở dữ liệu phân tán - Đăng ký học phần")
    print("=" * 60 + Colors.ENDC)
    print()

    # Validate template file
    if not Path(args.template).exists():
        log_error(f"Template file không tồn tại: {args.template}")
        sys.exit(1)

    # Kết nối Elasticsearch
    log_info(f"Kết nối Elasticsearch tại {args.host}...")

    try:
        es = Elasticsearch(
            [args.host],
            request_timeout=ES_TIMEOUT,
            retry_on_timeout=True,
            max_retries=3
        )

        # Verify connection
        if not es.ping():
            log_error("Không thể kết nối Elasticsearch!")
            sys.exit(1)

        log_success("Đã kết nối Elasticsearch")

    except Exception as e:
        log_error(f"Lỗi kết nối: {e}")
        sys.exit(1)

    # Chờ Elasticsearch healthy
    if not args.no_wait and not wait_for_elasticsearch(es):
        sys.exit(1)

    # Chế độ verify only
    if args.verify_only:
        list_elasticsearch_info(es)
        sys.exit(0)

    # Bước 1: Push template
    print()
    log_info("Bước 1/3: Push index template...")
    template_name = f"{args.index}_template"
    if not push_template(es, template_name, Path(args.template)):
        sys.exit(1)

    # Bước 2: Tạo index
    print()
    log_info("Bước 2/3: Tạo index...")
    if not check_and_create_index(es, args.index, Path(args.template), args):
        sys.exit(1)

    # Bước 3: Verify
    print()
    log_info("Bước 3/3: Kiểm tra cấu hình...")
    if not verify_setup(es, args.index):
        sys.exit(1)

    print()
    log_success("=" * 60)
    log_success("BOOTSTRAP HOÀN TẤT!")
    log_success("=" * 60)
    print()
    log_info(f"Index name: {args.index}")
    log_info(f"Template: {template_name}")
    log_info(f"ES Host: {args.host}")
    print()

    # List all info
    list_elasticsearch_info(es)


if __name__ == "__main__":
    main()
