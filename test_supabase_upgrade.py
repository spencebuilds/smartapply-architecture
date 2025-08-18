#!/usr/bin/env python3
"""
Test script for the Supabase upgrade integration.
"""

import logging
import os
from utils.logger import setup_logger


def test_supabase_upgrade():
    """Test the new Supabase upgrade functionality."""
    logger = setup_logger()
    logger.info("Testing Supabase upgrade integration")
    
    try:
        # Test imports
        from app.db.supabase_repo import SupabaseRepo
        from app.services.concept_extractor import ConceptExtractor
        from supabase import create_client
        
        logger.info("✓ All imports successful")
        
        # Test credentials
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            logger.error("✗ Supabase credentials not found")
            return False
        
        # Test repository
        repo = SupabaseRepo()
        logger.info("✓ Supabase repository initialized")
        
        # Test concept extractor
        sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        extractor = ConceptExtractor(sb)
        logger.info("✓ Concept extractor initialized")
        
        # Test basic operations
        stats = repo.get_database_stats()
        logger.info(f"✓ Database stats retrieved: {stats}")
        
        # Test concept extraction (with sample text)
        sample_text = "We are looking for a product manager with experience in API development and data analytics."
        concepts = extractor.extract(sample_text)
        logger.info(f"✓ Concept extraction test: found {len(concepts)} concepts: {concepts}")
        
        # Test company fetching
        companies = repo.get_companies_for_job_fetching()
        logger.info(f"✓ Company fetching test: found {len(companies)} companies")
        
        logger.info("✅ All Supabase upgrade tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Supabase upgrade test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_supabase_upgrade()
    if not success:
        exit(1)