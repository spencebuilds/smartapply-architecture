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
        """Fetch job postings for a specific company from Greenhouse with content."""
        try:
            # Try with content=true first for full job descriptions
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
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
            
            self.logger.info(f"Fetched {len(jobs)} jobs from Greenhouse for {company}")
            return jobs
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"No Greenhouse jobs available for {company}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching Greenhouse jobs for {company}: {str(e)}")
            return []
    
    def fetch_all_jobs(self, use_supabase: bool = True) -> List[Dict[str, Any]]:
        """Fetch all available job postings from Greenhouse."""
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
                    self.logger.warning("No companies found in Supabase, falling back to hardcoded list")
            except Exception as e:
                self.logger.warning(f"Error fetching companies from Supabase: {str(e)}, using fallback list")
        
        # Fallback to hardcoded list if Supabase is not available or empty
        if not companies:
            companies = [
                "stripe", "github", "shopify", "airbnb", "uber", "netflix", "spotify",
                "slack", "atlassian", "coinbase", "twitch", "square", "discord", "zoom",
                "asana", "dropbox", "pinterest", "palantir", "checkr", "gusto", "retool",
                "mixpanel", "amplitude", "buildkite", "apollo", "lattice", "workato",
                "greenhouse", "airtable", "loom", "linear", "superhuman", "notion",
                "figma", "robinhood", "plaid", "brex", "rippling", "zapier", "segment"
            ]
            self.logger.info("Using hardcoded company list")
        
        all_jobs = []
        for company in companies:
            jobs = self.fetch_jobs_for_company(company)
            all_jobs.extend(jobs)
        
        self.logger.info(f"Total jobs fetched from Greenhouse: {len(all_jobs)}")
        return all_jobs
    
    def fetch_jobs(self, companies: List[str] | None = None) -> List[Dict[str, Any]]:
        """Fetch job postings - now fetches all available jobs."""
        return self.fetch_all_jobs()
