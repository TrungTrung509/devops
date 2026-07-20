#!/bin/sh
# HEALTHCHECK - Elasticsearch

# Nhận tham số hoặc dùng mặc định
HOST="${ES_HOST:-localhost}"
PORT="${ES_PORT:-9200}"

# Kiểm tra health endpoint
curl -s "http://${HOST}:${PORT}/_cluster/health" 2>/dev/null | grep -q '"status":"green"\|"status":"yellow"'

if [ $? -eq 0 ]; then
    echo "Elasticsearch is ready"
    exit 0
else
    echo "Elasticsearch is not ready"
    exit 1
fi
