-- LOGICAL REPLICATION - SUBSCRIBER SETUP FOR HOALAC
-- DB-layer replicated tables: CoSo, Khoa, HocKy

DROP SUBSCRIPTION IF EXISTS sub_common_tables;

CREATE SUBSCRIPTION sub_common_tables
CONNECTION 'host=postgres_hadong port=5432 dbname=csdlpt_hadong user=csdlpt_user password=csdlpt_pass'
PUBLICATION pub_common_tables
WITH (
  copy_data = false,
  create_slot = true,
  enabled = true,
  slot_name = 'slot_hoalac'
);
