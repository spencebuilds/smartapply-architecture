#!/usr/bin/env python3
"""
Start the job monitoring system with Supabase learning integration.
"""

import sys
import logging
from main import JobApplicationSystem
from utils.logger import setup_logger


def main():
    """Start the enhanced job application system."""
    logger = setup_logger()
    logger.info("Starting Enhanced Job Application System with Supabase Learning")
    
    try:
        # Initialize and start the system
        system = JobApplicationSystem()
        
        # Verify Supabase integration
        if system.repo:
            stats = system.repo.get_database_stats()
            logger.info(f"Supabase integration active - Database stats: {stats}")
        else:
            logger.warning("Running without Supabase integration")
        
        # Start the system
        system.start()
        
    except KeyboardInterrupt:
        logger.info("Job monitoring stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in job monitoring: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()