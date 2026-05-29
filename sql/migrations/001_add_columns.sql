-- Run in Supabase SQL editor
-- (source column removed in 003_drop_source_column.sql)
alter table expenses add column if not exists raw_message text;
alter table expenses add column if not exists confidence float;
alter table expenses add column if not exists deleted_at timestamp;
