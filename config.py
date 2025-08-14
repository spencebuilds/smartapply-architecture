"""
Configuration settings for the job application system.
"""

import os
from typing import List


class Config:
    """Configuration class for job application system."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        
        # API Keys and Tokens
        self.LEVER_API_KEY = os.getenv("LEVER_API_KEY", "")
        self.GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY", "")
        self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
        self.SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")
        self.AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
        self.AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
        self.AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Job Applications")
        
        # Job Matching Configuration - back to 80% for PM roles
        self.MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "80.0"))
        
        # Target Companies (no longer used for filtering, kept for backward compatibility)
        companies_str = os.getenv("TARGET_COMPANIES", "")
        self.TARGET_COMPANIES = [company.strip() for company in companies_str.split(",") if company.strip()] if companies_str else []
        
        # Scheduling Configuration
        self.CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "job_application_system.log")
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        required_vars = [
            ("SLACK_BOT_TOKEN", self.SLACK_BOT_TOKEN),
            ("SLACK_CHANNEL_ID", self.SLACK_CHANNEL_ID),
            ("AIRTABLE_API_KEY", self.AIRTABLE_API_KEY),
            ("AIRTABLE_BASE_ID", self.AIRTABLE_BASE_ID),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # No longer require TARGET_COMPANIES since we fetch all available jobs
