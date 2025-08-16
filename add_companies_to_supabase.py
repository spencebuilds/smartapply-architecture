#!/usr/bin/env python3
"""
Script to add more companies to the Supabase database for testing.
"""

import logging
from api_clients.supabase_client import SupabaseClient
from utils.logger import setup_logger


def add_sample_companies():
    """Add sample companies to Supabase for testing."""
    logger = setup_logger()
    logger.info("Adding sample companies to Supabase")
    
    supabase_client = SupabaseClient()
    
    # Sample companies with worldview tags
    companies_to_add = [
        {
            'name': 'Stripe',
            'worldview_tags': ['fintech', 'platform-infrastructure', 'developer-tools'],
            'language_patterns': {'examples': ['payment platform', 'developer experience', 'infrastructure']}
        },
        {
            'name': 'Airbnb',
            'worldview_tags': ['marketplace', 'creator-ecosystem', 'trust-safety'],
            'language_patterns': {'examples': ['host experience', 'guest experience', 'marketplace']}
        },
        {
            'name': 'Slack',
            'worldview_tags': ['productivity-tools', 'developer-tools', 'collaboration'],
            'language_patterns': {'examples': ['workflow automation', 'collaboration', 'productivity']}
        },
        {
            'name': 'Notion',
            'worldview_tags': ['productivity-tools', 'creator-ecosystem', 'internal-tools'],
            'language_patterns': {'examples': ['workspace', 'productivity', 'knowledge management']}
        },
        {
            'name': 'GitHub',
            'worldview_tags': ['developer-tools', 'platform-infrastructure', 'collaboration'],
            'language_patterns': {'examples': ['developer experience', 'collaboration', 'version control']}
        }
    ]
    
    for company_data in companies_to_add:
        success = supabase_client.add_company(**company_data)
        if success:
            logger.info(f"Successfully added {company_data['name']}")
        else:
            logger.error(f"Failed to add {company_data['name']}")
    
    # Show updated statistics
    stats = supabase_client.get_database_stats()
    logger.info(f"Database now contains: {stats}")


if __name__ == "__main__":
    add_sample_companies()