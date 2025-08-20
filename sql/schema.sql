-- SmartApply Architecture - Database Schema (Rev A)
-- Sanitized version for public portfolio showcase
-- Real production schema with synthetic data only

-- Enable Row Level Security and UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core Tables

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255),
    worldview_tags TEXT[] DEFAULT '{}',
    language_patterns JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE concept_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_term VARCHAR(255) NOT NULL,
    concept_id UUID REFERENCES concepts(id),
    company_id UUID REFERENCES companies(id),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    successful_match_count INTEGER DEFAULT 0,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job System

CREATE TABLE job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255),
    company_id UUID REFERENCES companies(id),
    company_name VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    department VARCHAR(255),
    posting_url VARCHAR(1000),
    source VARCHAR(100),
    posting_date DATE,
    raw_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(external_id, source)
);

CREATE TABLE job_posting_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID REFERENCES job_postings(id) ON DELETE CASCADE,
    concept_id UUID REFERENCES concepts(id),
    confidence_score DECIMAL(3,2),
    extraction_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resume System

CREATE TABLE master_resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    version_name VARCHAR(255) NOT NULL,
    resume_text TEXT,
    file_url VARCHAR(1000),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE master_bullets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    category VARCHAR(100),
    original_text TEXT NOT NULL,
    concept_ids UUID[] DEFAULT '{}',
    usage_count INTEGER DEFAULT 0,
    effectiveness_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis System

CREATE TABLE role_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID REFERENCES job_postings(id),
    user_id UUID REFERENCES users(id),
    analyst_type VARCHAR(50) DEFAULT 'human',
    overall_fit_score DECIMAL(3,2) CHECK (overall_fit_score >= 0 AND overall_fit_score <= 1),
    fit_reasoning TEXT,
    key_matches JSONB DEFAULT '{}',
    vocabulary_gaps JSONB DEFAULT '{}',
    missing_requirements TEXT[] DEFAULT '{}',
    red_flags TEXT,
    optimization_strategy TEXT,
    resume_version_recommended VARCHAR(255),
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 10),
    estimated_application_priority VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE resume_optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_analysis_id UUID REFERENCES role_analyses(id),
    master_resume_id UUID REFERENCES master_resumes(id),
    optimization_deltas JSONB DEFAULT '{}',
    optimization_reasoning TEXT,
    optimized_resume_text TEXT,
    optimized_file_url VARCHAR(1000),
    vocabulary_translations JSONB DEFAULT '{}',
    case_studies_highlighted UUID[] DEFAULT '{}',
    ats_score_estimate DECIMAL(3,2),
    human_review_status VARCHAR(50) DEFAULT 'approved',
    human_review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE resume_deltas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_optimization_id UUID REFERENCES resume_optimizations(id) ON DELETE CASCADE,
    master_bullet_id UUID REFERENCES master_bullets(id),
    operation VARCHAR(20) CHECK (operation IN ('rephrase', 'reorder', 'emphasize', 'omit')),
    from_text TEXT NOT NULL,
    to_text TEXT,
    concept_ids UUID[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application Tracking

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    job_posting_id UUID REFERENCES job_postings(id),
    resume_optimization_id UUID REFERENCES resume_optimizations(id),
    status VARCHAR(50) DEFAULT 'applied',
    submitted_at TIMESTAMP WITH TIME ZONE,
    feedback TEXT,
    outcome VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, job_posting_id)
);

CREATE TABLE application_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning System

CREATE TABLE translation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    role_analysis_id UUID REFERENCES role_analyses(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50) DEFAULT 'success',
    original_terms TEXT[] DEFAULT '{}',
    translated_terms TEXT[] DEFAULT '{}',
    claude_api_used BOOLEAN DEFAULT false,
    api_cost DECIMAL(8,4) DEFAULT 0.0,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE translation_event_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    translation_event_id UUID REFERENCES translation_events(id) ON DELETE CASCADE,
    concept_mapping_id UUID REFERENCES concept_mappings(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Observability

CREATE TABLE company_term_styles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    term_pattern VARCHAR(255) NOT NULL,
    style_preference VARCHAR(255),
    confidence_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE ingest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,
    run_type VARCHAR(50),
    jobs_discovered INTEGER DEFAULT 0,
    jobs_processed INTEGER DEFAULT 0,
    jobs_matched INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    cost DECIMAL(8,4) DEFAULT 0.0,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE llm_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_hash VARCHAR(64) UNIQUE NOT NULL,
    prompt_text TEXT,
    response_text TEXT,
    model VARCHAR(100),
    tokens_used INTEGER,
    cost DECIMAL(8,4),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance

CREATE INDEX idx_concept_mappings_raw_term ON concept_mappings (lower(raw_term));
CREATE INDEX idx_concept_mappings_company ON concept_mappings (company_id);
CREATE INDEX idx_job_postings_company ON job_postings (company_id);
CREATE INDEX idx_job_postings_title ON job_postings (lower(title));
CREATE INDEX idx_role_analyses_job ON role_analyses (job_posting_id);
CREATE INDEX idx_role_analyses_user ON role_analyses (user_id);
CREATE INDEX idx_applications_user ON applications (user_id);
CREATE INDEX idx_translation_events_user ON translation_events (user_id);

-- Row Level Security (RLS) Policies

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_bullets ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_optimizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE translation_events ENABLE ROW LEVEL SECURITY;

-- Example RLS Policy (users can only see their own data)
CREATE POLICY user_own_data ON users FOR ALL USING (auth.uid() = id);
CREATE POLICY user_role_analyses ON role_analyses FOR ALL USING (auth.uid() = user_id);
CREATE POLICY user_resumes ON master_resumes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY user_bullets ON master_bullets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY user_applications ON applications FOR ALL USING (auth.uid() = user_id);

-- Functions and Triggers for Updated Timestamps

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concept_mappings_updated_at BEFORE UPDATE ON concept_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Note: This is a sanitized schema for portfolio demonstration.
-- Production includes additional constraints, triggers, and security policies.