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
            # Try the standard API endpoint first
            url = f"{self.base_url}/postings/{company}"
            headers = {"Accept": "application/json"}
            
            if self.config.LEVER_API_KEY:
                # Lever uses basic auth with API key as username and blank password
                import base64
                credentials = base64.b64encode(f"{self.config.LEVER_API_KEY}:".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check if we get a valid response
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        postings = data
                    elif isinstance(data, dict) and "data" in data:
                        postings = data["data"]
                    elif isinstance(data, dict) and data.get("ok") == False:
                        # API returned error response
                        self.logger.debug(f"Lever API error for {company}: {data.get('error', 'Unknown error')}")
                        return []
                    else:
                        postings = []
                    
                    jobs = []
                    for posting in postings:
                        # Parse job data with robust field handling
                        job = {
                            "id": f"lever_{posting.get('id', company + '_' + str(len(jobs)))}",
                            "title": posting.get("text", "") or posting.get("title", ""),
                            "company": company,
                            "description": posting.get("description", "") or posting.get("descriptionPlain", ""),
                            "location": self._extract_location(posting),
                            "department": self._extract_department(posting),
                            "url": posting.get("hostedUrl", "") or posting.get("applyUrl", ""),
                            "source": "lever",
                            "raw_data": posting
                        }
                        jobs.append(job)
                    
                    if jobs:
                        self.logger.info(f"Fetched {len(jobs)} jobs from Lever for {company}")
                    else:
                        self.logger.debug(f"No jobs found for {company} on Lever")
                    return jobs
                    
                except ValueError as e:
                    self.logger.debug(f"Invalid JSON response from Lever for {company}: {str(e)}")
                    return []
            else:
                self.logger.debug(f"Lever API returned {response.status_code} for {company}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"No Lever jobs available for {company}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching Lever jobs for {company}: {str(e)}")
            return []
    
    def _extract_location(self, posting: dict) -> str:
        """Extract location from Lever posting."""
        if "categories" in posting and "location" in posting["categories"]:
            return posting["categories"]["location"]
        elif "location" in posting:
            return posting["location"]
        elif "workplaceType" in posting:
            return posting["workplaceType"]
        return ""
    
    def _extract_department(self, posting: dict) -> str:
        """Extract department from Lever posting."""
        if "categories" in posting and "department" in posting["categories"]:
            return posting["categories"]["department"]
        elif "department" in posting:
            return posting["department"]
        elif "team" in posting:
            return posting["team"]
        return ""
    
    def discover_active_companies(self) -> List[str]:
        """Discover companies that actually have active job postings on Lever."""
        # Based on research, most companies have moved away from Lever's public API
        # or require authentication. Let's test a smaller, focused list.
        candidate_companies = [
            # Companies confirmed to use Lever (from investigation)
            "lever",  # Lever themselves
            # Potential active users (to test)
            "benchling", "flexport", "allbirds", "carta", "anthropic", "scale"
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
