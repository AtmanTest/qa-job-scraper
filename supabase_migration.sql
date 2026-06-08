create table if not exists public.jobs (
  id bigserial primary key,
  title text not null,
  company text,
  location text,
  url text unique not null,
  source text not null,
  description text,
  salary text,
  remote boolean default false,
  published_at timestamptz,
  scraped_at timestamptz default now(),
  tags text[] default '{}'
);
create index if not exists idx_jobs_source on public.jobs(source);
create index if not exists idx_jobs_scraped_at on public.jobs(scraped_at desc);
alter table public.jobs enable row level security;
create policy "public read" on public.jobs for select using (true);
create policy "service insert" on public.jobs for insert with check (true);
