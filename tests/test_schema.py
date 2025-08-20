"""
Basic schema validation tests for SmartApply architecture.
Portfolio demonstration of test patterns.
"""

import pytest
import os
import re


def test_schema_file_exists():
    """Ensure schema file exists in expected location."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    assert os.path.exists(schema_path), "Schema file should exist at sql/schema.sql"


def test_schema_contains_expected_tables():
    """Verify schema contains core tables."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_content = f.read().lower()
    
    expected_tables = [
        'users',
        'companies', 
        'concepts',
        'concept_mappings',
        'job_postings',
        'job_posting_concepts',
        'master_resumes',
        'master_bullets',
        'role_analyses',
        'resume_optimizations',
        'resume_deltas',
        'applications',
        'application_events',
        'translation_events',
        'translation_event_mappings',
        'company_term_styles',
        'ingest_runs',
        'api_calls',
        'llm_cache'
    ]
    
    for table in expected_tables:
        assert f'create table {table}' in schema_content or f'create table if not exists {table}' in schema_content, \
            f"Schema should contain {table} table"


def test_schema_uses_uuid_primary_keys():
    """Verify schema uses UUID primary keys."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_content = f.read()
    
    # Look for UUID primary key patterns
    uuid_pk_pattern = r'id UUID PRIMARY KEY DEFAULT gen_random_uuid\(\)'
    matches = re.findall(uuid_pk_pattern, schema_content, re.IGNORECASE)
    
    # Should have multiple UUID primary keys
    assert len(matches) >= 10, "Schema should use UUID primary keys for most tables"


def test_schema_includes_rls_policies():
    """Verify Row Level Security policies are present."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_content = f.read().lower()
    
    # Check for RLS enablement
    assert 'enable row level security' in schema_content, "Schema should enable RLS"
    assert 'create policy' in schema_content, "Schema should include RLS policies"


def test_schema_includes_indexes():
    """Verify strategic indexes are present."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_content = f.read().lower()
    
    # Check for index creation
    assert 'create index' in schema_content, "Schema should include performance indexes"
    
    # Check for specific strategic indexes
    expected_indexes = [
        'idx_concept_mappings_raw_term',
        'idx_job_postings_company',
        'idx_role_analyses_user'
    ]
    
    for index in expected_indexes:
        assert index.lower() in schema_content, f"Schema should include {index} index"


def test_schema_includes_audit_timestamps():
    """Verify audit timestamp columns are present."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_content = f.read().lower()
    
    # Check for timestamp columns
    assert 'created_at timestamp with time zone default now()' in schema_content, \
        "Schema should include created_at timestamps"
    assert 'updated_at timestamp with time zone default now()' in schema_content, \
        "Schema should include updated_at timestamps"


def test_demo_data_files_exist():
    """Verify demo data files are present."""
    demo_path = os.path.join(os.path.dirname(__file__), '..', 'demo', 'data')
    
    jobs_file = os.path.join(demo_path, 'synthetic_jobs.json')
    resume_file = os.path.join(demo_path, 'synthetic_resume.json')
    
    assert os.path.exists(jobs_file), "Synthetic jobs data should exist"
    assert os.path.exists(resume_file), "Synthetic resume data should exist"


def test_service_files_exist():
    """Verify service files are present."""
    services_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'services')
    
    expected_services = [
        'translator.py',
        'observability.py', 
        'resume_delta.py'
    ]
    
    for service in expected_services:
        service_path = os.path.join(services_path, service)
        assert os.path.exists(service_path), f"Service {service} should exist"


def test_documentation_files_exist():
    """Verify documentation is present."""
    docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    arch_doc = os.path.join(docs_path, 'architecture.md')
    system_diagram = os.path.join(docs_path, 'diagrams', 'system.mmd')
    
    assert os.path.exists(arch_doc), "Architecture documentation should exist"
    assert os.path.exists(system_diagram), "System diagram should exist"


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__])