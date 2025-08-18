#!/usr/bin/env python3
"""
Main entry point for the automated job application system.
Orchestrates job fetching, matching, and notifications.
"""

import logging
import time
import threading
import os
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

# New Supabase imports
from supabase import create_client, Client
from app.db.supabase_repo import SupabaseRepo
from app.services.concept_extractor import ConceptExtractor

# Initialize Supabase clients
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    SB: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    REPO = SupabaseRepo(SUPABASE_URL, SUPABASE_KEY)
    EXTRACTOR = ConceptExtractor(SB)
else:
    SB: Client | None = None
    REPO = None
    EXTRACTOR = None


class JobApplicationSystem:
    """Main job application automation system."""
    
    def __init__(self):
        """Initialize the job application system."""
        self.config = Config()
        self.logger = setup_logger()
        
        # Initialize API clients
        self.lever_client = LeverClient()
        self.greenhouse_client = GreenhouseClient()
        
        # Initialize optional clients based on configuration
        self.slack_client = SlackClient() if self.config.USE_SLACK else None
        self.airtable_client = AirtableClient() if self.config.USE_AIRTABLE else None
        
        # Initialize matching and storage
        self.keyword_matcher = KeywordMatcher()
        self.job_storage = JobStorage()
        
        # Initialize Supabase components
        self.sb = SB
        self.repo = REPO
        self.extractor = EXTRACTOR
        
        # Log integration status
        integrations = []
        if self.repo:
            integrations.append("Supabase")
        if self.slack_client and self.slack_client.enabled:
            integrations.append("Slack")
        if self.airtable_client and self.airtable_client.enabled:
            integrations.append("Airtable")
        
        if integrations:
            self.logger.info(f"Job Application System initialized with: {', '.join(integrations)}")
        else:
            self.logger.warning("Job Application System initialized without external integrations")
        
        self.logger.info("Job Application System initialized successfully")
    
    def fetch_all_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from all available sources."""
        all_jobs = []
        
        # Fetch from Lever - using Supabase company list if available
        try:
            lever_jobs = self.lever_client.fetch_all_jobs(use_supabase=bool(self.repo))
            all_jobs.extend(lever_jobs)
            self.logger.info(f"Fetched {len(lever_jobs)} jobs from Lever")
        except Exception as e:
            self.logger.error(f"Error fetching Lever jobs: {str(e)}")
        
        # Fetch from Greenhouse - using Supabase company list if available
        try:
            greenhouse_jobs = self.greenhouse_client.fetch_all_jobs(use_supabase=bool(self.repo))
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
                    
                    # Extract concepts using Supabase if available
                    if self.extractor:
                        try:
                            job["extracted_concepts"] = self.extractor.extract(job.get("description", ""))
                        except Exception as e:
                            self.logger.warning(f"Concept extraction failed for job {job['id']}: {str(e)}")
                            job["extracted_concepts"] = []
                    else:
                        job["extracted_concepts"] = []
                    
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
                # Send Slack notification (if enabled)
                if self.slack_client:
                    self.slack_client.send_job_notification(job)
                
                # Store in Airtable (if enabled)
                if self.airtable_client:
                    self.airtable_client.store_job(job)
                
                # Persist job + role analysis to Supabase (if available)
                if self.repo:
                    try:
                        fit_score = float(job["match_result"]["best_match_score"]) / 100.0
                        reasoning = job["match_result"].get("recommendation", "")
                        vocabulary_gaps = []  # Could be computed later
                        strategy = f"Use {job['match_result'].get('best_resume','')}"
                        
                        self.repo.store_job_analysis(
                            company_name=job.get("company", ""),
                            role_title=job.get("title", ""),
                            job_url=job.get("url", ""),
                            job_description=job.get("description", ""),
                            fit_score=fit_score,
                            reasoning=reasoning,
                            vocabulary_gaps=vocabulary_gaps,
                            optimization_strategy=strategy,
                        )
                        
                        self.logger.info(f"Stored job analysis in Supabase for {job['title']}")
                        
                    except Exception as e:
                        self.logger.warning(f"Supabase persistence failed for job {job.get('id', 'unknown')}: {e}")
                
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
