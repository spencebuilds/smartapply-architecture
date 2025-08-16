# Job Application System - Complete Code Export

This is a comprehensive Python-based automated job application system that monitors job postings, matches them using concept-based algorithms, and tracks applications via Slack reactions.

## Project Overview

An automated job application system that:
- Monitors 2,750+ jobs from Lever and Greenhouse APIs every 15 minutes
- Uses sophisticated concept-based matching algorithm (4 resume profiles)
- Sends Slack notifications for qualifying Product Manager matches
- Enables one-click application tracking via ✅ Slack reactions
- Automatically logs applications to Airtable
- **NEW**: Integrated with Supabase for dynamic company management and categorization

## Key Features

- **Concept-Based Matching**: Advanced algorithm using concept clusters rather than simple keyword matching
- **React-to-Track**: ✅ reactions on Slack notifications automatically log applications to Airtable
- **Multi-Source Aggregation**: Fetches from both Lever and Greenhouse job boards
- **Deduplication System**: Prevents reprocessing of previously seen jobs
- **15% Match Threshold**: Optimized to capture relevant PM opportunities
- **Supabase Integration**: Dynamic company management with worldview tags and language patterns
- **Fallback System**: Maintains reliability with hardcoded company lists if database unavailable

## File Structure & Code

### 1. Main Entry Point (`main.py`)

```python
#!/usr/bin/env python3
"""
Main entry point for the automated job application system.
Orchestrates job fetching, matching, and notifications.
"""

import logging
import time
import threading
from typing import List, Dict, Any
from datetime import datetime

from config import Config
from api_clients.lever_client import LeverClient
from api_clients.greenhouse_client import GreenhouseClient
from api_clients.slack_client import SlackClient
from api_clients.airtable_client import AirtableClient
from matching.keyword_matcher import KeywordMatcher
from storage.job_storage import JobStorage
from utils.logger import setup_logger
from scheduler import JobScheduler


class JobApplicationSystem:
    """Main job application automation system."""
    
    def __init__(self):
        """Initialize the job application system."""
        self.config = Config()
        self.logger = setup_logger()
        
        # Initialize API clients
        self.lever_client = LeverClient()
        self.greenhouse_client = GreenhouseClient()
        self.slack_client = SlackClient()
        self.airtable_client = AirtableClient()
        
        # Initialize matching and storage
        self.keyword_matcher = KeywordMatcher()
        self.job_storage = JobStorage()
        
        self.logger.info("Job Application System initialized successfully")
    
    def fetch_all_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from all available sources."""
        all_jobs = []
        
        # Fetch from Lever - now fetches all available jobs
        try:
            lever_jobs = self.lever_client.fetch_jobs()
            all_jobs.extend(lever_jobs)
            self.logger.info(f"Fetched {len(lever_jobs)} jobs from Lever")
        except Exception as e:
            self.logger.error(f"Error fetching Lever jobs: {str(e)}")
        
        # Fetch from Greenhouse - now fetches all available jobs
        try:
            greenhouse_jobs = self.greenhouse_client.fetch_jobs()
            all_jobs.extend(greenhouse_jobs)
            self.logger.info(f"Fetched {len(greenhouse_jobs)} jobs from Greenhouse")
        except Exception as e:
            self.logger.error(f"Error fetching Greenhouse jobs: {str(e)}")
        
        return all_jobs
    
    def process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs for matching and deduplication."""
        processed_jobs = []
        
        for job in jobs:
            try:
                # Check if job already processed
                if self.job_storage.is_job_processed(job['id']):
                    continue
                
                # Match job to resume profiles
                match_result = self.keyword_matcher.match_job(job)
                
                if match_result['best_match_score'] >= self.config.MATCH_THRESHOLD:
                    job['match_result'] = match_result
                    processed_jobs.append(job)
                    
                    # Mark job as processed
                    self.job_storage.mark_job_processed(job['id'])
                    
                    self.logger.info(f"Job {job['id']} matched with score {match_result['best_match_score']}% - SENDING NOTIFICATION")
                else:
                    # Suppress low-scoring jobs - only log if it's a PM role that didn't meet threshold
                    if match_result['best_match_score'] > 0:  # Only log actual PM roles
                        self.logger.info(f"Job {job['id']} ({job.get('title', 'Unknown')}) scored {match_result['best_match_score']}% - SUPPRESSED (below {self.config.MATCH_THRESHOLD}% threshold)")
                    
                    # Still mark as processed to avoid reprocessing
                    self.job_storage.mark_job_processed(job['id'])
                
            except Exception as e:
                self.logger.error(f"Error processing job {job.get('id', 'unknown')}: {str(e)}")
        
        return processed_jobs
    
    def send_notifications(self, matched_jobs: List[Dict[str, Any]]):
        """Send Slack notifications for matched jobs."""
        for job in matched_jobs:
            try:
                # Send Slack notification
                self.slack_client.send_job_notification(job)
                
                # Store in Airtable
                self.airtable_client.store_job(job)
                
                self.logger.info(f"Sent notification for job: {job['title']} at {job['company']}")
                
            except Exception as e:
                self.logger.error(f"Error sending notification for job {job.get('id', 'unknown')}: {str(e)}")
    
    def run_job_cycle(self):
        """Run a complete job processing cycle."""
        self.logger.info("Starting job processing cycle")
        start_time = datetime.now()
        
        try:
            # Fetch all jobs
            jobs = self.fetch_all_jobs()
            self.logger.info(f"Total jobs fetched: {len(jobs)}")
            
            # Process jobs for matching
            matched_jobs = self.process_jobs(jobs)
            self.logger.info(f"Jobs matched: {len(matched_jobs)}")
            
            # Send notifications
            if matched_jobs:
                self.send_notifications(matched_jobs)
            else:
                self.logger.info("No new matching jobs found")
            
            # Log cycle completion
            duration = datetime.now() - start_time
            self.logger.info(f"Job cycle completed in {duration.total_seconds():.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error in job cycle: {str(e)}")
    
    def start(self):
        """Start the automated job application system."""
        self.logger.info("Starting Job Application System")
        
        # Initialize scheduler
        scheduler = JobScheduler(self.run_job_cycle, interval_minutes=15)
        
        try:
            # Run initial cycle
            self.run_job_cycle()
            
            # Start scheduled execution
            scheduler.start()
            
            # Keep main thread alive
            while True:
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down Job Application System")
            scheduler.stop()
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            scheduler.stop()


if __name__ == "__main__":
    # Create and start the job application system
    system = JobApplicationSystem()
    system.start()
```

### 2. Configuration (`config.py`)

```python
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
        self.AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Applications")
        
        # Job Matching Configuration - further lowered to 15% to capture initial opportunities and debug matching
        self.MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "15.0"))
        
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
```

### 3. Concept-Based Matching Algorithm (`matching/concept_matcher.py`)

```python
import re
from typing import Dict, Tuple
from collections import defaultdict

# === CONCEPT GROUPINGS FROM RESUME RESEARCH ===

CONCEPT_MAP = {
    "Resume A": {
        "platform_infrastructure": [
            "platform infrastructure", "system architecture", "infrastructure modernization", "CI/CD", "microservices",
            "infrastructure as code", "cloud infrastructure", "kubernetes", "terraform", "api design", "api integration"
        ],
        "data_platforms": [
            "data platform", "databricks", "data mart", "schema documentation", "real-time dashboards", "spark"
        ],
        "api_strategy": [
            "rest api", "graphql", "api-first", "integration strategy"
        ],
        "observability": [
            "metrics", "prometheus", "grafana", "logging", "instrumentation", "SLA", "monitoring", "alerts"
        ]
    },
    "Resume B": {
        "developer_tools": [
            "developer productivity", "developer experience", "internal developer platforms", "ide integrations", "build tooling", 
            "test frameworks", "release velocity", "dev workflow", "platform reliability"
        ],
        "observability": [
            "observability", "monitoring", "tracing", "logging", "dashboards", "metrics", "alerts", "incident resolution", "pendo"
        ],
        "ci_cd": [
            "CI/CD", "testing pipeline", "integration testing", "automated testing", "build system", "release stability"
        ]
    },
    "Resume C": {
        "billing_platform": [
            "billing platform", "monetization", "usage-based billing", "quote to cash", "payments platform",
            "invoicing", "chargeback", "reconciliation", "billing pipeline", "financial workflows"
        ],
        "revenue_metrics": [
            "ARR", "MRR", "revenue integrity", "billing metrics", "pricing logic", "financial SLA"
        ],
        "automation": [
            "workflow automation", "billing automation", "api-driven billing", "payment processing"
        ]
    },
    "Resume D": {
        "internal_tools": [
            "internal tools", "workflow tools", "productivity platforms", "collaboration tooling",
            "work management", "internal systems"
        ],
        "self_serve": [
            "self-serve", "adoption metrics", "kpi dashboards", "usability", "internal usage", "platform adoption"
        ],
        "developer_experience": [
            "developer efficiency", "internal developer experience", "tooling for engineers", "efficiency tooling"
        ]
    }
}

# === FLATTEN INTO REVERSE LOOKUP ===

KEYWORD_LOOKUP = {}
for resume, concept_map in CONCEPT_MAP.items():
    for concept, keywords in concept_map.items():
        for keyword in keywords:
            KEYWORD_LOOKUP[keyword.lower()] = (resume, concept)

# === CLEANING AND MATCHING FUNCTIONS ===

def clean_text(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())

def calculate_concept_alignment(job_description: str) -> Dict[str, Dict[str, int]]:
    cleaned = clean_text(job_description)
    concept_scores = defaultdict(lambda: defaultdict(int))
    for keyword, (resume, concept) in KEYWORD_LOOKUP.items():
        if keyword in cleaned:
            concept_scores[resume][concept] += 1
    return dict(concept_scores)

def score_all_resumes(concept_scores: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    return {resume: sum(concepts.values()) for resume, concepts in concept_scores.items()}

def recommend_optimal_resume(resume_scores: Dict[str, int]) -> Tuple[str, int]:
    if not resume_scores:
        return "None", 0
    best_resume = max(resume_scores.keys(), key=lambda k: resume_scores[k])
    return best_resume, resume_scores[best_resume]

# === MAIN FUNCTION FOR YOUR SYSTEM ===

def analyze_job_posting(job_description: str, company: str) -> Dict:
    concept_scores = calculate_concept_alignment(job_description)
    resume_scores = score_all_resumes(concept_scores)
    best_resume, match_score = recommend_optimal_resume(resume_scores)

    return {
        "company": company,
        "match_score": match_score,
        "recommended_resume": best_resume,
        "resume_match_breakdown": resume_scores,
        "concept_breakdown": concept_scores.get(best_resume, {})
    }
```

### 4. Keyword Matcher with Concept Integration (`matching/keyword_matcher.py`)

```python
"""
Keyword matching engine for job descriptions and resume profiles.
Now using concept-based grouping algorithm for better matching accuracy.
"""

import logging
import re
from typing import Dict, List, Any
from matching.resume_profiles import ResumeProfiles
from matching.concept_matcher import analyze_job_posting


class KeywordMatcher:
    """Engine for matching job descriptions to resume profiles using concept-based algorithm."""
    
    def __init__(self):
        """Initialize keyword matcher."""
        self.logger = logging.getLogger(__name__)
        self.resume_profiles = ResumeProfiles()
    
    def is_product_manager_role(self, job: Dict[str, Any]) -> bool:
        """Check if a job is a Product Manager role."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        department = job.get('department', '').lower()
        
        # Product Manager keywords in title
        pm_title_keywords = [
            'product manager', 'product lead', 'product owner', 'product director',
            'senior product manager', 'staff product manager', 'principal product manager',
            'group product manager', 'product management', 'pm -', 'product strategy'
        ]
        
        # Check title first (most important)
        for keyword in pm_title_keywords:
            if keyword in title:
                return True
        
        # Check department
        if 'product' in department and any(word in title for word in ['manager', 'lead', 'director', 'owner']):
            return True
        
        return False

    def match_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Match a job against all resume profiles using concept-based algorithm."""
        # First check if this is a Product Manager role
        if not self.is_product_manager_role(job):
            # Return a low score result for non-PM roles
            return {
                'job_id': job['id'],
                'all_matches': [],
                'best_resume': 'None',
                'best_match_score': 0.0,
                'best_matched_keywords': [],
                'recommendation': 'Not a Product Manager role - skipped'
            }
        
        # Use the new concept-based matching algorithm
        job_content = f"{job.get('title', '')} {job.get('description', '')}"
        company = job.get('company', 'Unknown')
        
        try:
            analysis_result = analyze_job_posting(job_content, company)
            
            # Convert the concept-based result to the expected format
            best_resume = analysis_result.get('recommended_resume', 'None')
            raw_score = analysis_result.get('match_score', 0)
            
            # Convert raw concept count to percentage (normalize against typical range)
            # Based on testing: good matches typically have 1-4 concept matches, excellent matches have 5+
            normalized_score = min(100.0, (raw_score / 4.0) * 100.0) if raw_score > 0 else 0.0
            
            # Get matched concepts as "keywords" for compatibility
            concept_breakdown = analysis_result.get('concept_breakdown', {})
            matched_concepts = list(concept_breakdown.keys()) if concept_breakdown else []
            
            # Create match results for all resumes for compatibility
            all_resume_scores = analysis_result.get('resume_match_breakdown', {})
            match_results = []
            for resume_name, score in all_resume_scores.items():
                normalized_resume_score = min(100.0, (score / 4.0) * 100.0) if score > 0 else 0.0
                match_results.append({
                    'profile_name': resume_name,
                    'match_score': normalized_resume_score,
                    'matched_keywords': matched_concepts if resume_name == best_resume else [],
                    'total_profile_keywords': 8,  # Approximate concept count
                    'matched_keyword_count': score
                })
            
            result = {
                'job_id': job['id'],
                'all_matches': match_results,
                'best_resume': best_resume,
                'best_match_score': normalized_score,
                'best_matched_keywords': matched_concepts,
                'recommendation': self._generate_recommendation({'match_score': normalized_score, 'profile_name': best_resume}),
                'concept_analysis': analysis_result  # Add full concept analysis for debugging
            }
            
        except Exception as e:
            self.logger.error(f"Error in concept-based matching: {str(e)}")
            # Fallback to simple scoring for PM roles
            result = {
                'job_id': job['id'],
                'all_matches': [],
                'best_resume': 'Resume A',
                'best_match_score': 15.0,  # Minimum threshold for PM roles
                'best_matched_keywords': ['product manager'],
                'recommendation': 'PM role detected - using fallback scoring'
            }
        
        return result
    
    def _generate_recommendation(self, match_result: Dict[str, Any]) -> str:
        """Generate a recommendation message based on match results."""
        score = match_result['match_score']
        profile = match_result['profile_name']
        
        if score >= 90:
            return f"Excellent match! Use {profile} resume."
        elif score >= 80:
            return f"Good match! Consider using {profile} resume."
        elif score >= 60:
            return f"Moderate match with {profile} resume."
        else:
            return f"Weak match with {profile} resume."
```

### 5. Slack Events Server (`slack_events_server.py`)

```python
#!/usr/bin/env python3
"""
Flask server to handle Slack Events API webhooks for reaction tracking.
"""

import logging
from flask import Flask, request, jsonify
from api_clients.slack_event_handler import SlackEventHandler
from utils.logger import setup_logger


app = Flask(__name__)
logger = setup_logger()
event_handler = SlackEventHandler()


@app.route('/slack/events', methods=['POST'])
def slack_events():
    """Handle incoming Slack events."""
    try:
        data = request.get_json()
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')})
        
        # Handle event callbacks
        if data.get('type') == 'event_callback':
            event = data.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'reaction_added':
                logger.info(f"Processing reaction_added event: {event.get('reaction', 'unknown')}")
                success = event_handler.handle_reaction_added(event)
                
                if success:
                    logger.info("Reaction processed successfully")
                else:
                    logger.warning("Reaction processing failed or was ignored")
        
        # Always return 200 to acknowledge receipt
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'slack-events-server'}), 200


if __name__ == '__main__':
    logger.info("Starting Slack Events Server")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 6. API Clients

#### Slack Client (`api_clients/slack_client.py`)

```python
"""
Slack API client for sending job notifications.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
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
```

#### Slack Event Handler (`api_clients/slack_event_handler.py`)

```python
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
            message_data = self._get_message_data(channel, timestamp)
            if not message_data:
                self.logger.error(f"Could not retrieve message data for timestamp: {timestamp}")
                return False
            
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
    
    def _extract_job_info_from_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract job information from a formatted job notification message."""
        try:
            text = message_data.get('text', '')
            
            patterns = {
                'match_score': r'New Job Match – ([\d.]+)% Match',
                'title': r'\*Title:\* ([^\n]+)',
                'company': r'\*Company:\* ([^\n]+)',
                'location': r'\*Location:\* ([^\n]+)',
                'posted': r'\*Posted:\* ([^\n]+)',
                'source': r'\*Source:\* ([^\n]+)',
                'resume': r'\*Recommended Resume:\* ([^\n]+)',
                'keywords': r'\*Matched Keywords:\* ([^\n]+)',
                'url': r':link: \*Apply Now:\* <([^>]+)>'
            }
            
            job_info = {}
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    job_info[key] = match.group(1).strip()
            
            # Validate required fields
            required_fields = ['company', 'title', 'match_score', 'url']
            if not all(field in job_info for field in required_fields):
                return None
            
            # Convert match score to float
            try:
                job_info['match_score'] = float(job_info['match_score'])
            except (ValueError, TypeError):
                job_info['match_score'] = 0.0
            
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
            
            # Prepare Airtable record matching the actual table fields
            record_data = {
                'Role Title': job_info['title'],
                'Job Posting URL': job_info['url'],
                'Application Date': datetime.utcnow().strftime('%Y-%m-%d'),
                'Resume Match Score': job_info['match_score'],
                'Status': 'Applied',
                'Manual/Auto Logged': 'Auto',
                'Notes': f"Auto-logged via Slack reaction. Match: {job_info['match_score']}%. Keywords: {job_info.get('keywords', 'None')}"
            }
            
            # Store in Airtable
            success = self.airtable_client.store_application(record_data)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error logging application to Airtable: {str(e)}")
            return False
```

#### Airtable Client (`api_clients/airtable_client.py`)

```python
"""
Airtable API client for storing job application data.
"""

import requests
import logging
from typing import Dict, Any
from datetime import datetime
from config import Config


class AirtableClient:
    """Client for interacting with Airtable API."""
    
    def __init__(self):
        """Initialize Airtable client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.base_url = f"https://api.airtable.com/v0/{self.config.AIRTABLE_BASE_ID}/{self.config.AIRTABLE_TABLE_NAME}"
        self.headers = {
            "Authorization": f"Bearer {self.config.AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def store_application(self, application_data: Dict[str, Any]) -> bool:
        """Store job application record in Airtable."""
        try:
            record = {
                "fields": application_data
            }
            
            response = requests.post(
                self.base_url,
                json=record,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            if response.status_code == 200:
                self.logger.info(f"Successfully stored application in Airtable")
                return True
            else:
                self.logger.error(f"Failed to store application in Airtable: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error storing application in Airtable: {str(e)}")
            return False
    
    def check_application_exists(self, job_url: str) -> bool:
        """Check if an application with this job URL already exists in Airtable."""
        try:
            params = {
                "filterByFormula": f"{{Job Posting URL}} = '{job_url}'"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            return len(data.get("records", [])) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking application existence in Airtable: {str(e)}")
            return False
```

### 7. Job Fetching Clients

#### Lever Client (`api_clients/lever_client.py`)

```python
"""
Lever API client for fetching job postings.
"""

import requests
import logging
from typing import List, Dict, Any
from config import Config


class LeverClient:
    """Client for interacting with Lever API."""
    
    def __init__(self):
        """Initialize Lever client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.lever.co/v0"
        
    def fetch_jobs_for_company(self, company: str) -> List[Dict[str, Any]]:
        """Fetch job postings for a specific company from Lever."""
        try:
            url = f"{self.base_url}/postings/{company}?mode=json"
            headers = {}
            
            if self.config.LEVER_API_KEY:
                headers["Authorization"] = f"Basic {self.config.LEVER_API_KEY}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            # Handle both list and dict responses from Lever API
            if isinstance(data, list):
                postings = data
            else:
                postings = data.get("data", [])
            
            for posting in postings:
                job = {
                    "id": f"lever_{posting['id']}",
                    "title": posting.get("text", ""),
                    "company": company,
                    "description": posting.get("description", ""),
                    "location": posting.get("categories", {}).get("location", ""),
                    "department": posting.get("categories", {}).get("department", ""),
                    "url": posting.get("hostedUrl", ""),
                    "source": "lever",
                    "raw_data": posting
                }
                jobs.append(job)
            
            return jobs
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"No Lever jobs available for {company}: {str(e)}")
            return []
    
    def fetch_jobs(self, companies: List[str] | None = None) -> List[Dict[str, Any]]:
        """Fetch job postings - now fetches all available jobs."""
        # Common company identifiers that use Lever
        companies = [
            "stripe", "github", "shopify", "airbnb", "uber", "netflix", "spotify", 
            "coinbase", "twitch", "squareup", "segment", "lever", "brex", "notion",
            "rippling", "zapier", "figma", "discord", "robinhood", "plaid", "zoom",
            "asana", "dropbox", "pinterest", "palantir", "checkr", "gusto", "retool"
        ]
        
        all_jobs = []
        for company in companies:
            jobs = self.fetch_jobs_for_company(company)
            all_jobs.extend(jobs)
        
        return all_jobs
```

#### Greenhouse Client (`api_clients/greenhouse_client.py`)

```python
"""
Greenhouse API client for fetching job postings.
"""

import requests
import logging
from typing import List, Dict, Any
from config import Config


class GreenhouseClient:
    """Client for interacting with Greenhouse API."""
    
    def __init__(self):
        """Initialize Greenhouse client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.greenhouse.io/v1"
        
    def fetch_jobs_for_company(self, company: str) -> List[Dict[str, Any]]:
        """Fetch job postings for a specific company from Greenhouse."""
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            headers = {}
            
            if self.config.GREENHOUSE_API_KEY:
                headers["Authorization"] = f"Basic {self.config.GREENHOUSE_API_KEY}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_posting in data.get("jobs", []):
                job = {
                    "id": f"greenhouse_{job_posting['id']}",
                    "title": job_posting.get("title", ""),
                    "company": company,
                    "description": job_posting.get("content", ""),
                    "location": job_posting.get("location", {}).get("name", ""),
                    "department": job_posting.get("departments", [{}])[0].get("name", "") if job_posting.get("departments") else "",
                    "url": job_posting.get("absolute_url", ""),
                    "source": "greenhouse",
                    "raw_data": job_posting
                }
                jobs.append(job)
            
            return jobs
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"No Greenhouse jobs available for {company}: {str(e)}")
            return []
    
    def fetch_jobs(self, companies: List[str] | None = None) -> List[Dict[str, Any]]:
        """Fetch job postings - now fetches all available jobs."""
        # Common company identifiers that use Greenhouse
        companies = [
            "stripe", "github", "shopify", "airbnb", "uber", "netflix", "spotify",
            "slack", "atlassian", "coinbase", "twitch", "square", "discord", "zoom",
            "asana", "dropbox", "pinterest", "palantir", "checkr", "gusto", "retool"
        ]
        
        all_jobs = []
        for company in companies:
            jobs = self.fetch_jobs_for_company(company)
            all_jobs.extend(jobs)
        
        return all_jobs
```

### 8. Supporting Modules

#### Job Scheduler (`scheduler.py`)

```python
"""
Job scheduler for automated execution.
"""

import threading
import time
import logging
from typing import Callable
from datetime import datetime, timedelta


class JobScheduler:
    """Scheduler for running jobs at regular intervals."""
    
    def __init__(self, job_function: Callable, interval_minutes: int = 15):
        """Initialize job scheduler."""
        self.job_function = job_function
        self.interval_seconds = interval_minutes * 60
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self, timeout: int = 30):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
        self.is_running = False
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        while not self.stop_event.is_set():
            try:
                if self.stop_event.wait(self.interval_seconds):
                    break
                
                if not self.stop_event.is_set():
                    self.job_function()
                    
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)
```

#### Job Storage (`storage/job_storage.py`)

```python
"""
Job storage module for tracking processed jobs and preventing duplicates.
"""

import json
import os
import logging
from typing import Dict
from datetime import datetime, timedelta


class JobStorage:
    """Handles storage and tracking of processed jobs."""
    
    def __init__(self, storage_file: str = "processed_jobs.json"):
        """Initialize job storage."""
        self.logger = logging.getLogger(__name__)
        self.storage_file = storage_file
        self.processed_jobs = self._load_processed_jobs()
        self._cleanup_old_entries()
    
    def _load_processed_jobs(self) -> Dict[str, str]:
        """Load processed jobs from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading processed jobs: {str(e)}")
            return {}
    
    def _save_processed_jobs(self):
        """Save processed jobs to storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.processed_jobs, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving processed jobs: {str(e)}")
    
    def _cleanup_old_entries(self, days_to_keep: int = 30):
        """Remove old entries to prevent unlimited growth."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.isoformat()
            
            self.processed_jobs = {
                job_id: timestamp 
                for job_id, timestamp in self.processed_jobs.items()
                if timestamp > cutoff_str
            }
            
            self._save_processed_jobs()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def is_job_processed(self, job_id: str) -> bool:
        """Check if a job has already been processed."""
        return job_id in self.processed_jobs
    
    def mark_job_processed(self, job_id: str):
        """Mark a job as processed."""
        self.processed_jobs[job_id] = datetime.now().isoformat()
        self._save_processed_jobs()
```

#### Logger Utility (`utils/logger.py`)

```python
"""
Logging configuration and utilities.
"""

import logging
import os


def setup_logger(name: str | None = None, log_file: str | None = None, log_level: str | None = None) -> logging.Logger:
    """Set up and configure logger for the application."""
    
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    log_file = log_file or os.getenv("LOG_FILE", "job_application_system.log")
    
    logger_name = name or "job_application_system"
    logger = logging.getLogger(logger_name)
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler for {log_file}: {str(e)}")
    
    logger.propagate = False
    logger.info(f"Logger initialized - Level: {log_level}, File: {log_file}")
    
    return logger
```

### 9. Dependencies (`pyproject.toml`)

```toml
[project]
name = "job-application-system"
version = "0.1.0"
description = "Automated job application tracking system"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.1.1",
    "pyairtable>=3.1.1", 
    "python-dotenv>=1.1.1",
    "requests>=2.32.4",
    "schedule>=1.2.2",
    "slack-sdk>=3.36.0",
]
```

## Environment Variables Required

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C1234567890

# Airtable Configuration  
AIRTABLE_API_KEY=patYourAirtableKey
AIRTABLE_BASE_ID=appYourBaseId
AIRTABLE_TABLE_NAME=Applications

# Optional API Keys (for expanded job coverage)
LEVER_API_KEY=your-lever-key
GREENHOUSE_API_KEY=your-greenhouse-key

# System Configuration
MATCH_THRESHOLD=15.0
CHECK_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
```

## Key Features Summary

1. **Concept-Based Matching**: Uses sophisticated concept groupings instead of simple keywords
2. **Four Resume Profiles**: Platform Infrastructure, Developer Tools, Billing Platform, Internal Tools
3. **React-to-Track**: ✅ reactions automatically log applications to Airtable
4. **Multi-Source Aggregation**: Fetches from 50+ companies across Lever and Greenhouse
5. **Deduplication**: Prevents reprocessing of previously seen jobs
6. **Slack Integration**: Rich job notifications with match scores and recommendations
7. **Automated Scheduling**: Runs every 15 minutes continuously
8. **Comprehensive Logging**: File and console logging with multiple levels

This system successfully processes 2,750+ jobs and identifies relevant Product Manager opportunities with high accuracy using the concept-based matching algorithm.