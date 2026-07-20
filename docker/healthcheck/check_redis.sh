#!/bin/sh
# HEALTHCHECK - Redis

HOST="${REDIS_HOST:-localhost}"
PORT="${REDIS_PORT:-6379}"

# Kiểm tra redis-cli ping
redis-cli -h "$HOST" -p "$PORT" ping > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Redis is ready"
    exit 0
else
    echo "Redis is not ready"
    exit 1
fi
