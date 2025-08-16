#!/usr/bin/env python3
"""
Test script for Supabase integration.
"""

import logging
from api_clients.supabase_client import SupabaseClient
from utils.logger import setup_logger


def test_supabase_integration():
    """Test the Supabase integration functionality."""
    logger = setup_logger()
    logger.info("Starting Supabase integration test")
    
    # Initialize Supabase client
    supabase_client = SupabaseClient()
    
    # Test 1: Get all companies
    logger.info("Test 1: Fetching all companies")
    companies = supabase_client.get_all_companies()
    logger.info(f"Found {len(companies)} total companies")
    
    if companies:
        # Show first few companies
        for i, company in enumerate(companies[:3]):
            logger.info(f"Company {i+1}: {company}")
    
    # Test 2: Get companies by tag
    logger.info("\nTest 2: Fetching companies by worldview tag")
    
    gaming_companies = supabase_client.get_companies_by_tag('gaming-first')
    logger.info(f"Found {len(gaming_companies)} gaming-first companies")
    
    creator_companies = supabase_client.get_companies_by_tag('creator-ecosystem')
    logger.info(f"Found {len(creator_companies)} creator-ecosystem companies")
    
    # Test 3: Get company names for job fetching
    logger.info("\nTest 3: Fetching company names for job API calls")
    
    company_names = supabase_client.get_company_names_for_job_fetching()
    logger.info(f"Company names for job fetching: {company_names}")  # Show all since there's only 1
    
    # Test 4: Search companies
    logger.info("\nTest 4: Searching companies")
    
    search_results = supabase_client.search_companies('stripe')
    logger.info(f"Search results for 'stripe': {search_results}")
    
    # Test 5: Get database stats
    logger.info("\nTest 5: Database statistics")
    
    stats = supabase_client.get_database_stats()
    logger.info(f"Database stats: {stats}")
    
    logger.info("Supabase integration test completed")


if __name__ == "__main__":
    test_supabase_integration()