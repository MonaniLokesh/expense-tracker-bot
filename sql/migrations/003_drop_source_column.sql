-- Run in Supabase SQL editor (after backups if needed)
alter table expenses drop column if exists source;
