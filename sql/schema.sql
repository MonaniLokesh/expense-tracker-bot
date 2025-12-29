create table expenses (
    id uuid primary key default gen_random_uuid(),
    user_id bigint not null,
    amount numeric not null,
    category text not null,
    description text,
    expense_date date not null,
    created_at timestamp default now()
);
