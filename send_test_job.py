#!/usr/bin/env python3
"""
Send a test Product Manager job to Slack.
"""

from api_clients.slack_client import SlackClient
from utils.logger import setup_logger

def send_test_pm_job():
    """Send a test Product Manager job notification."""
    logger = setup_logger()
    
    # Create a realistic test PM job with new formatting
    test_job = {
        "id": "test_pm_002",
        "title": "Staff Product Manager - Platform Infrastructure",
        "company": "Palantir",
        "description": "Lead product strategy for our platform infrastructure, working on Kubernetes, microservices, and scalable architecture.",
        "location": "Washington, D.C.",
        "department": "Product",
        "url": "https://jobs.lever.co/palantir/test-staff-pm",
        "source": "lever",
        "posted_date": "2025-08-14",
        "match_result": {
            "best_resume": "Resume_A_Platform_Infrastructure",
            "best_match_score": 94.0,
            "best_matched_keywords": ["platform", "kubernetes", "infrastructure", "microservices", "scalable", "architecture"],
            "recommendation": "Perfect match for platform infrastructure PM role"
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