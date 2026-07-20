
-- LOGICAL REPLICATION - PUBLISHER SETUP (HADONG)
-- Shared tables replicated at DB layer:
--   - CoSo
--   - Khoa
--   - HocKy
--
-- Not replicated here:
--   - HocPhan: replicated at app layer via ReplicationService
--   - users: distributed writes managed by the app

-- PostgreSQL server must start with:
--   wal_level = logical
--   max_replication_slots = 10
--   max_wal_senders = 10

-- Slot creation is handled by CREATE SUBSCRIPTION with create_slot = true.
-- Do not pre-create physical slots here for logical replication.

-- Recreate publication to keep the table list explicit.
DROP PUBLICATION IF EXISTS pub_common_tables;

CREATE PUBLICATION pub_common_tables FOR TABLE
    "CoSo",
    "Khoa",
    "HocKy";

-- Verification:
-- SELECT * FROM pg_publication;
-- SELECT pubname, tablename
-- FROM pg_publication_tables
-- WHERE pubname = 'pub_common_tables';
