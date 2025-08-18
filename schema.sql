-- Enable UUID generator (Supabase Postgres has pgcrypto available)
create extension if not exists pgcrypto;

-- 1) USERS
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  name text,
  working_style text,
  strengths text,
  career_goals text,
  risk_tolerance text,
  created_at timestamp default now()
);

-- 2) COMPANIES
create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text unique,
  language_patterns text[],
  worldview_tags text[],
  created_at timestamp default now()
);

-- 3) CONCEPTS
create table if not exists concepts (
  id uuid primary key default gen_random_uuid(),
  name text unique not null
);

-- 4) RESUMES (master template & versions)
create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  name text,
  summary text,
  experience jsonb,
  skills text[],
  education jsonb,
  certifications text[],
  created_at timestamp default now()
);

-- 5) CASE STUDIES
create table if not exists case_studies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  title text,
  description text,
  quantified_results text,
  demonstrated_skills text[],
  created_at timestamp default now()
);

-- 6) JOB POSTINGS
create table if not exists job_postings (
  id uuid primary key default gen_random_uuid(),
  company_name text,
  role_title text,
  job_url text unique,
  job_description text,
  posted_at timestamp,
  company_id uuid references companies(id) on delete set null,
  extracted_concepts text[] default '{}',
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 7) ROLE ANALYSIS
create table if not exists role_analysis (
  id uuid primary key default gen_random_uuid(),
  job_posting_id uuid references job_postings(id) on delete cascade,
  fit_score numeric,
  reasoning text,
  vocabulary_gaps text[],
  optimization_strategy text,
  created_at timestamp default now()
);

-- 8) RESUME OPTIMIZATIONS
create table if not exists resume_optimizations (
  id uuid primary key default gen_random_uuid(),
  job_posting_id uuid references job_postings(id) on delete cascade,
  resume_id uuid references resumes(id) on delete set null,
  changes_applied text,
  justification text,
  optimized_resume jsonb,
  created_at timestamp default now()
);

-- 9) APPLICATIONS
create table if not exists applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  job_posting_id uuid references job_postings(id) on delete cascade,
  resume_id uuid references resumes(id) on delete set null,
  status text check (status in ('applied','interview','offer','rejected')),
  feedback text,
  submitted_at timestamp,
  updated_at timestamp default now()
);

-- 10) CONCEPT MAPPINGS (raw term -> concept)
create table if not exists concept_mappings (
  id uuid primary key default gen_random_uuid(),
  raw_term text,
  concept_id uuid references concepts(id) on delete cascade,
  user_id uuid references users(id) on delete set null,
  company_id uuid references companies(id) on delete set null,
  confidence_score numeric,
  successful_match_count integer default 0,
  created_at timestamp default now()
);

-- 11) TRANSLATION EVENTS (learning log)
create table if not exists translation_events (
  id uuid primary key default gen_random_uuid(),
  concept_mapping_id uuid references concept_mappings(id) on delete cascade,
  application_id uuid references applications(id) on delete cascade,
  event_type text,
  timestamp timestamp default now()
);

-- Indexes
create index if not exists idx_job_postings_company on job_postings(company_id);
create index if not exists idx_job_postings_url on job_postings(job_url);
create index if not exists idx_concept_mappings_raw on concept_mappings(raw_term);
create index if not exists idx_concept_mappings_concept on concept_mappings(concept_id);
create index if not exists idx_translation_events_app on translation_events(application_id);

-- updated_at trigger
create or replace function update_timestamp() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_job_postings_updated on job_postings;
create trigger trg_job_postings_updated
before update on job_postings
for each row execute function update_timestamp();