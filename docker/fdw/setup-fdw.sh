#!/bin/sh
# set -eu replaced with manual error handling for ash compatibility

wait_for_db() {
  host="$1"
  db="$2"
  user="$3"

  until pg_isready -h "$host" -p 5432 -U "$user" -d "$db" >/dev/null 2>&1; do
    echo "Waiting for $host/$db ..."
    sleep 2
  done
}

run_sql() {
  host="$1"
  db="$2"
  user="$3"
  password="$4"
  file="$5"

  echo "Applying $(basename "$file") to $host/$db"
  PGPASSWORD="$password" psql \
    -v ON_ERROR_STOP=1 \
    -h "$host" \
    -p 5432 \
    -U "$user" \
    -d "$db" \
    -f "$file"
}

wait_for_db postgres_hadong "$HADONG_DB" "$HADONG_USER"
wait_for_db postgres_ngoctruc "$NGOCTRUC_DB" "$NGOCTRUC_USER"
wait_for_db postgres_hoalac "$HOALAC_DB" "$HOALAC_USER"

run_sql postgres_hadong "$HADONG_DB" "$HADONG_USER" "$HADONG_PASSWORD" /sql/fdw/01_hadong_fdw.sql
run_sql postgres_ngoctruc "$NGOCTRUC_DB" "$NGOCTRUC_USER" "$NGOCTRUC_PASSWORD" /sql/fdw/02_ngoctruc_fdw.sql
run_sql postgres_hoalac "$HOALAC_DB" "$HOALAC_USER" "$HOALAC_PASSWORD" /sql/fdw/03_hoalac_fdw.sql

run_sql postgres_hadong "$HADONG_DB" "$HADONG_USER" "$HADONG_PASSWORD" /sql/views/01_hadong_distributed_views.sql
run_sql postgres_ngoctruc "$NGOCTRUC_DB" "$NGOCTRUC_USER" "$NGOCTRUC_PASSWORD" /sql/views/02_ngoctruc_distributed_views.sql
run_sql postgres_hoalac "$HOALAC_DB" "$HOALAC_USER" "$HOALAC_PASSWORD" /sql/views/03_hoalac_distributed_views.sql

echo "FDW bootstrap completed."
