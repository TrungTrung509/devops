#!/bin/bash
# BENCHMARK SCRIPT - Centralized vs Distributed

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "  BENCHMARK: Centralized vs Distributed"
echo ""

# Copy centralized queries
docker cp "$PROJECT_ROOT/sql/benchmark/centralized_queries.sql" csdlpt_centralized:/tmp/centralized_queries.sql

# Copy distributed queries
docker cp "$PROJECT_ROOT/sql/benchmark/distributed_queries.sql" csdlpt_hadong:/tmp/distributed_queries.sql

echo "[1/2] Running centralized queries..."
docker exec csdlpt_centralized psql -U csdlpt_user -d csdlpt_centralized -f /tmp/centralized_queries.sql

echo ""
echo "[2/2] Running distributed queries (HADONG with FDW)..."
docker exec csdlpt_hadong psql -U csdlpt_user -d csdlpt_hadong -f /tmp/distributed_queries.sql

echo ""
echo "Done. To save results, redirect output to a file."
echo "Example: $0 > docs/benchmark/results.txt"
