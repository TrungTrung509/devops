
-- LOGICAL REPLICATION - SUBSCRIBER SETUP
-- Run this script on NGOCTRUC and HOALAC separately.
--
-- DB-layer replicated tables:
--   - CoSo
--   - Khoa
--   - HocKy
--
-- App-layer replicated tables:
--   - HocPhan
--
-- App-managed distributed writes:
--   - users

-- Before running:
-- 1. Common tables already exist on the subscriber.
-- 2. Publication pub_common_tables already exists on HADONG.
-- 3. Replace slot_name for each subscriber:
--      NGOCTRUC -> slot_ngoctruc
--      HOALAC   -> slot_hoalac

DROP SUBSCRIPTION IF EXISTS sub_common_tables;

CREATE SUBSCRIPTION sub_common_tables
CONNECTION 'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass'
PUBLICATION pub_common_tables
WITH (
  copy_data = false,
  create_slot = true,
  enabled = true,
  slot_name = 'slot_ngoctruc'
);

-- Notes:
-- - copy_data = false means existing rows are NOT backfilled automatically.
-- - Only changes made after the subscription starts will be streamed.
-- - For HOALAC, change slot_name above to 'slot_hoalac' before running.

-- Verification:
-- SELECT * FROM pg_subscription;
-- SELECT * FROM pg_stat_subscription;
-- SELECT * FROM pg_subscription_rel;
