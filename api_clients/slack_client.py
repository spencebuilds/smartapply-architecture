"""
Slack API client for sending job notifications.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config import Config

# Optional Slack imports (only if enabled)
try:
    config = Config()
    if config.USE_SLACK:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    else:
        WebClient = None
        SlackApiError = Exception
except ImportError:
    WebClient = None
    SlackApiError = Exception


class SlackClient:
    """Client for sending Slack notifications."""
    
    def __init__(self):
        """Initialize Slack client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        if self.config.USE_SLACK and WebClient:
            self.client = WebClient(token=self.config.SLACK_BOT_TOKEN)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            self.logger.info("Slack integration disabled")
    
    def format_job_message(self, job: Dict[str, Any]) -> str:
        """Format job information using the new template format."""
        match_result = job.get('match_result', {})
        best_resume = match_result.get('best_resume', 'Unknown')
        match_score = match_result.get('best_match_score', 0)
        matched_keywords = match_result.get('best_matched_keywords', [])
        
        # Format resume display name
        resume_display = "Unknown"
        if "Resume_A" in best_resume:
            resume_display = "Resume A - Platform Infrastructure"
        elif "Resume_B" in best_resume:
            resume_display = "Resume B - Developer Tools & Observability"
        elif "Resume_C" in best_resume:
            resume_display = "Resume C - Billing & Revenue Platform"
        
        # Get job age if available
        job_age = self._get_job_age(job)
        time_posted = job_age if job_age else "Recently"
        
        # Determine source from job data
        source = job.get('source', 'Unknown').title()
        
        # Format matched keywords
        keywords_text = ', '.join(matched_keywords) if matched_keywords else 'None'
        
        # Build message using proper Slack formatting
        message = f"""🎯 *New Job Match – {match_score}% Match*

*Title:* {job['title']}  
*Company:* {job['company']}  
*Location:* {job.get('location', 'Not specified')}  
*Posted:* {time_posted}  
*Source:* {source}

*Match Score:* {match_score}%  
*Recommended Resume:* {resume_display}  
*Matched Keywords:* {keywords_text}

🔗 *Apply Now:* <{job.get('url', '#')}>  
✅ React with ✅ after applying to log it in Airtable."""
        
        return message
    
    def _get_job_age(self, job: Dict[str, Any]) -> Optional[str]:
        """Determine job posting age from available data."""
        # Try to extract date from various possible fields
        date_fields = ['posted_date', 'created_at', 'date_posted', 'published_at']
        
        for field in date_fields:
            if field in job and job[field]:
                try:
                    # Handle different date formats
                    job_date_str = job[field]
                    
                    # Common date formats to try
                    date_formats = [
                        '%Y-%m-%d',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%Y-%m-%dT%H:%M:%S.%fZ',
                        '%m/%d/%Y',
                        '%d/%m/%Y'
                    ]
                    
                    job_date = None
                    for fmt in date_formats:
                        try:
                            job_date = datetime.strptime(job_date_str.split('T')[0] if 'T' in job_date_str else job_date_str, fmt.split('T')[0] if 'T' in fmt else fmt)
                            break
                        except ValueError:
                            continue
                    
                    if job_date:
                        days_ago = (datetime.now() - job_date).days
                        
                        if days_ago == 0:
                            return "Today"
                        elif days_ago == 1:
                            return "1 day ago"
                        elif days_ago <= 7:
                            return f"{days_ago} days ago"
                        elif days_ago <= 30:
                            weeks = days_ago // 7
                            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
                        else:
                            return "30+ days ago"
                            
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def send_job_notification(self, job: Dict[str, Any]) -> bool:
        """Send a job notification to the configured Slack channel."""
        if not self.enabled:
            self.logger.debug(f"Slack disabled, skipping notification for job: {job.get('title', 'Unknown')}")
            return True  # Return success to not break workflow
        
        try:
            message = self.format_job_message(job)
            
            response = self.client.chat_postMessage(
                channel=self.config.SLACK_CHANNEL_ID,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            
            if response["ok"]:
                self.logger.info(f"Successfully sent Slack notification for job: {job['id']}")
                return True
            else:
                self.logger.error(f"Failed to send Slack notification: {response.get('error', 'Unknown error')}")
                return False
                
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack notification: {str(e)}")
            return False
    
    def send_status_message(self, message: str) -> bool:
        """Send a general status message to the Slack channel."""
        if not self.enabled:
            self.logger.debug(f"Slack disabled, skipping status message: {message}")
            return True  # Return success to not break workflow
        
        try:
            response = self.client.chat_postMessage(
                channel=self.config.SLACK_CHANNEL_ID,
                text=f"🤖 Job Bot Status: {message}"
            )
            
            return response["ok"]
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error sending status: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending status message: {str(e)}")
            return False
