-- FIXED SCHEMA: Drop existing tables and recreate with correct types
-- This addresses the foreign key constraint error by ensuring consistent UUID types

-- Enable UUID generator (Supabase Postgres has pgcrypto available)
create extension if not exists pgcrypto;

-- DROP existing tables to fix type mismatches (in correct order due to dependencies)
drop table if exists translation_events cascade;
drop table if exists applications cascade;
drop table if exists concept_mappings cascade;
drop table if exists role_analysis cascade;
drop table if exists job_postings cascade;
drop table if exists case_studies cascade;
drop table if exists resumes cascade;
drop table if exists concepts cascade;
drop table if exists companies cascade;
drop table if exists users cascade;

-- 1) USERS
create table users (
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
create table companies (
  id uuid primary key default gen_random_uuid(),
  name text unique,
  language_patterns text[],
  worldview_tags text[],
  created_at timestamp default now()
);

-- 3) CONCEPTS
create table concepts (
  id uuid primary key default gen_random_uuid(),
  name text unique not null
);

-- 4) RESUMES (master template & versions)
create table resumes (
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
create table case_studies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  title text,
  description text,
  quantified_results text,
  demonstrated_skills text[],
  created_at timestamp default now()
);

-- 6) JOB POSTINGS
create table job_postings (
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
create table role_analysis (
  id uuid primary key default gen_random_uuid(),
  job_posting_id uuid references job_postings(id) on delete cascade,
  fit_score numeric,
  reasoning text,
  vocabulary_gaps text[],
  optimization_strategy text,
  created_at timestamp default now()
);

-- 8) CONCEPT MAPPINGS (core ML table)
create table concept_mappings (
  id uuid primary key default gen_random_uuid(),
  raw_term text not null,
  concept_id uuid references concepts(id) on delete cascade,
  confidence_score numeric default 0.5 check (confidence_score >= 0.0 and confidence_score <= 1.0),
  successful_match_count integer default 0,
  user_id uuid references users(id) on delete set null,
  company_id uuid references companies(id) on delete set null,
  created_at timestamp default now()
);

-- 9) APPLICATIONS (track what gets applied to)
create table applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  job_posting_id uuid references job_postings(id) on delete cascade,
  resume_id uuid references resumes(id) on delete set null,
  status text default 'applied',
  feedback text,
  submitted_at timestamp default now(),
  updated_at timestamp default now()
);

-- 10) TRANSLATION EVENTS (ML learning events)
create table translation_events (
  id uuid primary key default gen_random_uuid(),
  concept_mapping_id uuid references concept_mappings(id) on delete cascade,
  application_id uuid references applications(id) on delete cascade,
  event_type text default 'success',
  created_at timestamp default now()
);

-- INDEXES for performance
create index if not exists idx_job_postings_company_id on job_postings(company_id);
create index if not exists idx_job_postings_url on job_postings(job_url);
create index if not exists idx_concept_mappings_term on concept_mappings(raw_term);
create index if not exists idx_concept_mappings_concept_id on concept_mappings(concept_id);
create index if not exists idx_applications_user_job on applications(user_id, job_posting_id);

-- RLS (Row Level Security) setup for multi-user support
alter table users enable row level security;
alter table resumes enable row level security;
alter table case_studies enable row level security;
alter table applications enable row level security;

-- Basic RLS policies (can be customized later)
create policy "Users can view own data" on users for select using (auth.uid() = id);
create policy "Users can update own data" on users for update using (auth.uid() = id);

-- Insert sample data to test the schema
-- Sample companies
insert into companies (name, worldview_tags, language_patterns) values
  ('Epic Games', array['gaming-first', 'creator-ecosystem'], array['game', 'player', 'creator', 'metaverse']),
  ('Stripe', array['fintech', 'platform-thinking'], array['payment', 'developer', 'platform', 'infrastructure']),
  ('Slack', array['communication', 'productivity'], array['collaboration', 'team', 'workflow', 'integration']),
  ('Notion', array['productivity', 'knowledge-work'], array['workspace', 'knowledge', 'database', 'template'])
on conflict (name) do nothing;

-- Sample concepts
insert into concepts (name) values
  ('Product Management'),
  ('API Development'),
  ('Data Analytics'),
  ('User Experience'),
  ('Growth Strategy')
on conflict (name) do nothing;

-- Sample concept mappings
insert into concept_mappings (raw_term, concept_id, confidence_score) 
select 'product manager', c.id, 0.9 from concepts c where c.name = 'Product Management'
union all
select 'pm role', c.id, 0.8 from concepts c where c.name = 'Product Management'  
union all
select 'api design', c.id, 0.9 from concepts c where c.name = 'API Development'
union all
select 'data-driven', c.id, 0.7 from concepts c where c.name = 'Data Analytics'
union all
select 'user research', c.id, 0.8 from concepts c where c.name = 'User Experience';

-- Display success message
select 'Schema created successfully!' as status;