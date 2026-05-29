-- Fix: "new row violates row-level security policy for table expenses"
--
-- BEST: use service_role key in .env SUPABASE_KEY (Settings → API → service_role secret).
-- That bypasses RLS for your backend bot.
--
-- OR run this if you want to keep the anon key:

alter table expenses enable row level security;

drop policy if exists "expenses_bot_all" on expenses;
create policy "expenses_bot_all" on expenses
  for all
  using (true)
  with check (true);
