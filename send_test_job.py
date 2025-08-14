#!/usr/bin/env python3
"""
Send a test Product Manager job to Slack.
"""

from api_clients.slack_client import SlackClient
from utils.logger import setup_logger

def send_test_pm_job():
    """Send a test Product Manager job notification."""
    logger = setup_logger()
    
    # Create a realistic test PM job
    test_job = {
        "id": "test_pm_001",
        "title": "Senior Product Manager - Billing Platform",
        "company": "TestCorp",
        "description": "Lead product strategy for our billing and payments platform, working on pricing models, subscription management, and revenue optimization.",
        "location": "San Francisco, CA",
        "department": "Product",
        "url": "https://example.com/jobs/test-pm",
        "source": "test",
        "match_result": {
            "best_resume": "Resume_C_Billing_Revenue_Platform",
            "best_match_score": 92.0,
            "best_matched_keywords": ["billing", "pricing", "payments", "revenue", "subscription"],
            "recommendation": "Excellent match for billing platform PM role"
        }
    }
    
    slack_client = SlackClient()
    success = slack_client.send_job_notification(test_job)
    
    if success:
        logger.info("Test PM job sent to Slack successfully!")
    else:
        logger.error("Failed to send test job")
    
    return success

if __name__ == "__main__":
    send_test_pm_job()