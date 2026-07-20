CREATE TABLE IF NOT EXISTS benchmark_run (
    id BIGSERIAL PRIMARY KEY,
    run_label TEXT,
    dataset_note TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS benchmark_result (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES benchmark_run(id) ON DELETE CASCADE,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    query_code TEXT NOT NULL,
    query_name TEXT NOT NULL,
    query_type TEXT NOT NULL,

    model TEXT NOT NULL CHECK (model IN ('centralized', 'distributed')),

    execution_time_ms DOUBLE PRECISION NOT NULL,
    planning_time_ms DOUBLE PRECISION,
    total_time_ms DOUBLE PRECISION,

    used_fdw BOOLEAN NOT NULL DEFAULT FALSE,
    rows_returned INTEGER
);

CREATE INDEX IF NOT EXISTS idx_benchmark_result_run_id
ON benchmark_result(run_id);

CREATE INDEX IF NOT EXISTS idx_benchmark_result_measured_at
ON benchmark_result(measured_at);

CREATE OR REPLACE VIEW v_benchmark_latest AS
SELECT br.*
FROM benchmark_result br
WHERE br.run_id = (
    SELECT MAX(id)
    FROM benchmark_run
);

CREATE OR REPLACE VIEW v_benchmark_compare_latest AS
WITH latest AS (
    SELECT MAX(id) AS run_id
    FROM benchmark_run
),
pivoted AS (
    SELECT
        br.query_code,
        MAX(br.query_name) AS query_name,
        MAX(br.query_type) AS query_type,

        MAX(br.execution_time_ms) FILTER (WHERE br.model = 'centralized') AS centralized_ms,
        MAX(br.execution_time_ms) FILTER (WHERE br.model = 'distributed') AS distributed_ms,

        BOOL_OR(br.used_fdw) AS used_fdw
    FROM benchmark_result br
    JOIN latest l ON br.run_id = l.run_id
    GROUP BY br.query_code
)
SELECT
    query_code,
    query_name,
    query_type,
    centralized_ms,
    distributed_ms,
    used_fdw,
    CASE
        WHEN centralized_ms < distributed_ms THEN 'Centralized'
        WHEN distributed_ms < centralized_ms THEN 'Distributed'
        ELSE 'Equal'
    END AS faster_model,
    ROUND(
        (
            GREATEST(centralized_ms, distributed_ms)
            / NULLIF(LEAST(centralized_ms, distributed_ms), 0)
        )::numeric,
        2
    ) AS difference_ratio
FROM pivoted
ORDER BY query_code;