"""
Slack API client for sending job notifications.
"""

import logging
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import Config


class SlackClient:
    """Client for sending Slack notifications."""
    
    def __init__(self):
        """Initialize Slack client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.client = WebClient(token=self.config.SLACK_BOT_TOKEN)
    
    def format_job_message(self, job: Dict[str, Any]) -> str:
        """Format job information into a Slack message."""
        match_result = job.get('match_result', {})
        best_resume = match_result.get('best_resume', 'Unknown')
        match_score = match_result.get('best_match_score', 0)
        
        message = f"""🎯 *New Job Match Found!*

*Job Title:* {job['title']}
*Company:* {job['company']}
*Location:* {job.get('location', 'Not specified')}
*Department:* {job.get('department', 'Not specified')}

*Match Details:*
• Recommended Resume: *{best_resume}*
• Match Score: *{match_score}%*

*Job Description Preview:*
{job.get('description', 'No description available')[:300]}...

*Apply Here:* {job.get('url', 'URL not available')}

Source: {job.get('source', 'Unknown').title()}
Job ID: {job['id']}
"""
        return message
    
    def send_job_notification(self, job: Dict[str, Any]) -> bool:
        """Send a job notification to the configured Slack channel."""
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
