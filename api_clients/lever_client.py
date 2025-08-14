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
            url = f"{self.base_url}/postings/{company}"
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
            self.logger.error(f"Error fetching Lever jobs for {company}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching Lever jobs for {company}: {str(e)}")
            return []
    
    def fetch_jobs(self, companies: List[str]) -> List[Dict[str, Any]]:
        """Fetch job postings for multiple companies from Lever."""
        all_jobs = []
        
        for company in companies:
            jobs = self.fetch_jobs_for_company(company)
            all_jobs.extend(jobs)
        
        return all_jobs
