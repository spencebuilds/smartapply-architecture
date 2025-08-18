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
            
            self.logger.info(f"Fetched {len(jobs)} jobs from Lever for {company}")
            return jobs
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"No Lever jobs available for {company}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching Lever jobs for {company}: {str(e)}")
            return []
    
    def discover_active_companies(self) -> List[str]:
        """Discover companies that actually have active job postings on Lever."""
        candidate_companies = [
            # Tech companies likely to use Lever
            "netflix", "uber", "github", "shopify", "slack", "atlassian", "postmates",
            "flexport", "benchling", "allbirds", "carta", "discord", "figma", "notion", 
            "linear", "retool", "vercel", "anthropic", "scale", "nuro", "cruise", "waymo",
            "mongodb", "elastic", "confluent", "snowflake", "datadog", "okta", "crowdstrike",
            "zscaler", "pagerduty", "newrelic", "splunk", "hashicorp", "gitlab", "docker"
        ]
        
        active_companies = []
        self.logger.info(f"Testing {len(candidate_companies)} companies for active Lever job postings...")
        
        for company in candidate_companies:
            try:
                jobs = self.fetch_jobs_for_company(company)
                if jobs:
                    active_companies.append(company)
                    self.logger.info(f"✅ {company}: {len(jobs)} active jobs")
            except Exception:
                continue
        
        self.logger.info(f"Found {len(active_companies)} companies with active Lever postings")
        return active_companies

    def fetch_all_jobs(self, use_supabase: bool = True) -> List[Dict[str, Any]]:
        """Fetch all available job postings from Lever by discovering active companies."""
        companies = []
        
        if use_supabase:
            try:
                from api_clients.supabase_client import SupabaseClient
                supabase_client = SupabaseClient()
                supabase_companies = supabase_client.get_company_names_for_job_fetching()
                if supabase_companies:
                    companies = supabase_companies
                    self.logger.info(f"Using {len(companies)} companies from Supabase")
                else:
                    self.logger.warning("No companies found in Supabase, discovering active companies")
            except Exception as e:
                self.logger.warning(f"Error fetching companies from Supabase: {str(e)}, discovering active companies")
        
        # Discover active companies if no Supabase data
        if not companies:
            companies = self.discover_active_companies()
        
        all_jobs = []
        for company in companies:
            jobs = self.fetch_jobs_for_company(company)
            all_jobs.extend(jobs)
        
        self.logger.info(f"Total jobs fetched from Lever: {len(all_jobs)}")
        return all_jobs
    
    def fetch_jobs(self, companies: List[str] | None = None) -> List[Dict[str, Any]]:
        """Fetch job postings - now fetches all available jobs."""
        return self.fetch_all_jobs()
