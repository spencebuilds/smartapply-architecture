"""
Slack Events API handler for processing reactions and tracking job applications.
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import Config
from api_clients.airtable_client import AirtableClient


class SlackEventHandler:
    """Handles Slack events for job application tracking."""
    
    def __init__(self):
        """Initialize Slack event handler."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.client = WebClient(token=self.config.SLACK_BOT_TOKEN)
        self.airtable_client = AirtableClient()
    
    def handle_reaction_added(self, event_data: Dict[str, Any]) -> bool:
        """Handle reaction_added events from Slack."""
        try:
            reaction = event_data.get('reaction', '')
            user = event_data.get('user', '')
            channel = event_data.get('item', {}).get('channel', '')
            timestamp = event_data.get('item', {}).get('ts', '')
            
            # Only process ✅ reactions
            if reaction != 'white_check_mark':
                self.logger.debug(f"Ignoring non-checkmark reaction: {reaction}")
                return False
            
            # Only process reactions in our configured channel
            if channel != self.config.SLACK_CHANNEL_ID:
                self.logger.debug(f"Ignoring reaction in different channel: {channel}")
                return False
            
            # Get the original message
            self.logger.info(f"Retrieving message from channel {channel} at timestamp {timestamp}")
            message_data = self._get_message_data(channel, timestamp)
            if not message_data:
                self.logger.error(f"Could not retrieve message data for timestamp: {timestamp}")
                return False
            
            self.logger.info(f"Retrieved message data: {message_data.get('text', 'No text field')[:100]}...")
            
            # Extract job information from the message
            job_info = self._extract_job_info_from_message(message_data)
            if not job_info:
                self.logger.warning("Could not extract job information from message")
                return False
            
            # Log application to Airtable
            success = self._log_application_to_airtable(job_info, user)
            
            if success:
                self.logger.info(f"Successfully logged application for {job_info['company']} - {job_info['title']}")
                # Send confirmation reaction
                self._add_confirmation_reaction(channel, timestamp)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error handling reaction_added event: {str(e)}")
            return False
    
    def _get_message_data(self, channel: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """Retrieve message data from Slack."""
        try:
            self.logger.info(f"Calling conversations_history for channel={channel}, timestamp={timestamp}")
            response = self.client.conversations_history(
                channel=channel,
                latest=timestamp,
                limit=1,
                inclusive=True
            )
            
            self.logger.info(f"Slack API response ok: {response.get('ok')}, messages count: {len(response.get('messages', []))}")
            
            if response["ok"] and response["messages"]:
                message = response["messages"][0]
                self.logger.info(f"Message timestamp: {message.get('ts')}, expected: {timestamp}")
                return message
            else:
                self.logger.warning(f"No messages found or API error: {response}")
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error retrieving message: {e.response['error']}")
        except Exception as e:
            self.logger.error(f"Error retrieving message: {str(e)}")
        
        return None
    
    def _extract_job_info_from_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract job information from a formatted job notification message."""
        try:
            text = message_data.get('text', '')
            
            # Parse the Slack formatted message:
            # 🎯 *New Job Match – 94% Match*
            # *Title:* Staff Product Manager - Platform Infrastructure  
            # *Company:* Palantir  
            # *Location:* Washington, D.C.  
            # *Posted:* Today  
            # *Source:* Lever
            # *Match Score:* 94%  
            # *Recommended Resume:* Resume A - Platform Infrastructure  
            # *Matched Keywords:* platform, kubernetes, infrastructure
            # 🔗 *Apply Now:* <url>  
            # ✅ React with ✅ after applying to log it in Airtable.
            
            patterns = {
                'match_score': r'New Job Match – (\d+)% Match',
                'title': r'\*Title:\* ([^\n]+)',
                'company': r'\*Company:\* ([^\n]+)',
                'location': r'\*Location:\* ([^\n]+)',
                'posted': r'\*Posted:\* ([^\n]+)',
                'source': r'\*Source:\* ([^\n]+)',
                'resume': r'\*Recommended Resume:\* ([^\n]+)',
                'keywords': r'\*Matched Keywords:\* ([^\n]+)',
                'url': r'🔗 \*Apply Now:\* <([^>]+)>'
            }
            
            job_info = {}
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    job_info[key] = match.group(1).strip()
            
            # Validate required fields
            required_fields = ['company', 'title', 'match_score', 'url']
            if not all(field in job_info for field in required_fields):
                self.logger.warning(f"Missing required fields in job info: {job_info}")
                self.logger.warning(f"Message text preview: {text[:200]}...")
                # Log which patterns matched for debugging
                for key, pattern in patterns.items():
                    match = re.search(pattern, text)
                    if match:
                        self.logger.info(f"Pattern '{key}' matched: {match.group(1)}")
                    else:
                        self.logger.warning(f"Pattern '{key}' failed to match")
                return None
            
            # Convert match score to float
            try:
                job_info['match_score'] = float(job_info['match_score'])
            except (ValueError, TypeError):
                job_info['match_score'] = 0.0
            
            # Set defaults for optional fields
            job_info.setdefault('location', 'Not specified')
            job_info.setdefault('resume', 'Unknown')
            job_info.setdefault('posted', 'Unknown')
            job_info.setdefault('keywords', 'None')
            job_info.setdefault('source', 'Unknown')
            
            return job_info
            
        except Exception as e:
            self.logger.error(f"Error extracting job info from message: {str(e)}")
            return None
    
    def _log_application_to_airtable(self, job_info: Dict[str, Any], user_id: str) -> bool:
        """Log job application to Airtable with deduplication."""
        try:
            # Check if application already exists (deduplication by job URL)
            if self.airtable_client.check_application_exists(job_info['url']):
                self.logger.info(f"Application already logged for URL: {job_info['url']}")
                return True
            
            # Prepare Airtable record
            record_data = {
                'Company': job_info['company'],
                'Title': job_info['title'],
                'Applied Date': datetime.utcnow().isoformat(),
                'Resume Used': job_info['resume'],
                'Match Score': job_info['match_score'],
                'Job Link': job_info['url'],
                'Source': self._determine_source(job_info['url']),
                'Status': 'Applied',
                'Location': job_info['location'],
                'Keywords': job_info['keywords'],
                'User ID': user_id
            }
            
            # Store in Airtable
            success = self.airtable_client.store_application(record_data)
            
            if success:
                self.logger.info(f"Application logged to Airtable: {job_info['company']} - {job_info['title']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error logging application to Airtable: {str(e)}")
            return False
    

    
    def _determine_source(self, job_url: str) -> str:
        """Determine job source from URL."""
        if 'lever.co' in job_url.lower():
            return 'Lever'
        elif 'greenhouse.io' in job_url.lower() or 'boards.greenhouse.io' in job_url.lower():
            return 'Greenhouse'
        else:
            return 'Unknown'
    
    def _add_confirmation_reaction(self, channel: str, timestamp: str) -> bool:
        """Add a confirmation reaction to show the application was logged."""
        try:
            response = self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name='heavy_check_mark'  # ✔️ emoji
            )
            return response["ok"]
        except SlackApiError as e:
            # Ignore if reaction already exists
            if e.response['error'] == 'already_reacted':
                return True
            self.logger.error(f"Error adding confirmation reaction: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Error adding confirmation reaction: {str(e)}")
            return False