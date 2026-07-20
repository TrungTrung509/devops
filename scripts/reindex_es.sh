#!/bin/bash
# REINDEX ELASTICSEARCH - Đẩy dữ liệu vào Elasticsearch

set -e

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "  REINDEX ELASTICSEARCH"
echo ""

# Thư mục gốc
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SEEDS_DIR="$PROJECT_ROOT/seeds"

# BƯỚC 1: Bootstrap Elasticsearch (tạo index/template)
echo -e "${BLUE}[1/2] Bootstrap Elasticsearch...${NC}"

cd "$PROJECT_ROOT"

# Chạy bootstrap script
python scripts/bootstrap_search.py --force

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Bootstrap Elasticsearch thất bại${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Bootstrap Elasticsearch thành công${NC}"
echo ""

# BƯỚC 2: Reindex dữ liệu
echo -e "${BLUE}[2/2] Reindex dữ liệu từ PostgreSQL...${NC}"

python scripts/reindex_es.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Reindex thất bại${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Reindex thành công${NC}"
echo ""

# HOÀN TẤT
echo -e "${CYAN}=========================================="
echo -e "  REINDEX HOÀN TẤT!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}Elasticsearch endpoints:${NC}"
echo "  - Index: http://localhost:9200/hocphan"
echo "  - Kibana: http://localhost:5601"
echo ""
