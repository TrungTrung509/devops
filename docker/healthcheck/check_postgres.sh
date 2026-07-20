#!/bin/sh
# HEALTHCHECK - PostgreSQL
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
USER="${POSTGRES_USER:-csdlpt_user}"
DB="${POSTGRES_DB:-csdlpt_hadong}"

# Kiểm tra pg_isready
pg_isready -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "PostgreSQL is ready"
    exit 0
else
    echo "PostgreSQL is not ready"
    exit 1
fi
