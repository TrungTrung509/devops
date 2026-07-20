# SQL Replication

This folder configures PostgreSQL logical replication for the shared tables that are now managed at the DB layer.

## Scope

DB-layer logical replication:
- `CoSo`
- `Khoa`
- `HocKy`

App-layer replication:
- `HocPhan`

App-managed distributed writes:
- `users`

## Topology

- Publisher: `HADONG`
- Subscribers: `NGOCTRUC`, `HOALAC`
- Direction: one-way replication from `HADONG` to the other two sites

## Files

- [`01_setup_publisher.sql`](/d:/CSDLPT/BTL-CSDLPT/sql/replication/01_setup_publisher.sql)
- [`02_setup_subscribers.sql`](/d:/CSDLPT/BTL-CSDLPT/sql/replication/02_setup_subscribers.sql)

## Required PostgreSQL settings

The PostgreSQL containers must start with logical replication enabled, for example:

```yaml
command:
  - postgres
  - "-c"
  - wal_level=logical
  - "-c"
  - max_replication_slots=10
  - "-c"
  - max_wal_senders=10
```

## Important behavior

- `copy_data = false` is used in the subscriber script.
- Existing rows are not copied automatically.
- Only changes made after the subscription is created will be replicated.

## Execution order

1. Run `01_setup_publisher.sql` on `csdlpt_hadong`.
2. Run `02_setup_subscribers.sql` on `csdlpt_ngoctruc`.
3. Run `02_setup_subscribers.sql` on `csdlpt_hoalac`, but change `slot_name` to `slot_hoalac` first.

`01_setup_publisher.sql` does not pre-create slots. Each subscription creates its own logical slot with `create_slot = true`.

## Verification

On the publisher:

```sql
SELECT * FROM pg_publication;

SELECT pubname, tablename
FROM pg_publication_tables
WHERE pubname = 'pub_common_tables';
```

On each subscriber:

```sql
SELECT * FROM pg_subscription;
SELECT * FROM pg_stat_subscription;
SELECT * FROM pg_subscription_rel;
```

Expected shared tables in the publication:

```sql
SELECT 'CoSo' AS tbl, COUNT(*) AS cnt FROM "CoSo"
UNION ALL
SELECT 'Khoa', COUNT(*) FROM "Khoa"
UNION ALL
SELECT 'HocKy', COUNT(*) FROM "HocKy";
```
