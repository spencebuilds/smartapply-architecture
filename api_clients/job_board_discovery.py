"""
Dynamic job board discovery for Lever and Greenhouse APIs.
Discovers all available companies with active job postings.
"""

import requests
import logging
import time
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os


class JobBoardDiscovery:
    """Discovers all available companies on Lever and Greenhouse job boards."""
    
    def __init__(self):
        """Initialize job board discovery."""
        self.logger = logging.getLogger(__name__)
        self.cache_file = "discovered_companies.json"
        self.cache_ttl_hours = 24  # Cache for 24 hours
        
    def load_cached_companies(self) -> Dict[str, Any]:
        """Load cached company discovery results."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                # Check if cache is still valid
                cache_time = data.get('timestamp', 0)
                current_time = time.time()
                if current_time - cache_time < (self.cache_ttl_hours * 3600):
                    self.logger.info(f"Using cached company data from {self.cache_file}")
                    return data
                    
            return {}
        except Exception as e:
            self.logger.warning(f"Error loading cache: {e}")
            return {}
    
    def save_cached_companies(self, companies_data: Dict[str, Any]):
        """Save discovered companies to cache."""
        try:
            companies_data['timestamp'] = time.time()
            with open(self.cache_file, 'w') as f:
                json.dump(companies_data, f, indent=2)
            self.logger.info(f"Saved {len(companies_data.get('greenhouse', []))} Greenhouse + {len(companies_data.get('lever', []))} Lever companies to cache")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def discover_greenhouse_companies(self) -> List[str]:
        """Discover all active Greenhouse companies by testing common company patterns."""
        self.logger.info("Discovering Greenhouse companies...")
        
        # Start with known working companies and expand
        seed_companies = [
            'stripe', 'airbnb', 'coinbase', 'figma', 'discord', 'dropbox', 
            'asana', 'pinterest', 'robinhood', 'plaid', 'brex', 'segment',
            'amplitude', 'buildkite', 'lattice', 'greenhouse', 'airtable',
            'loom', 'linear', 'superhuman', 'zapier', 'rippling'
        ]
        
        # Add common tech company patterns
        tech_patterns = [
            'github', 'shopify', 'uber', 'netflix', 'spotify', 'slack', 
            'atlassian', 'twitch', 'square', 'zoom', 'notion', 'mongodb',
            'elastic', 'confluent', 'snowflake', 'datadog', 'okta', 
            'crowdstrike', 'zscaler', 'pagerduty', 'newrelic', 'splunk'
        ]
        
        all_candidates = seed_companies + tech_patterns
        working_companies = []
        
        def test_company(company):
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('jobs', [])
                    if jobs and len(jobs) > 0:
                        # Verify jobs have content
                        sample_content_len = len(jobs[0].get('content', ''))
                        return {
                            'company': company,
                            'job_count': len(jobs),
                            'has_content': sample_content_len > 100
                        }
                return None
            except Exception as e:
                return None
        
        # Test companies in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_company = {executor.submit(test_company, company): company for company in all_candidates}
            
            for future in as_completed(future_to_company):
                result = future.result()
                if result:
                    working_companies.append(result)
                    self.logger.info(f"✅ Found Greenhouse: {result['company']} ({result['job_count']} jobs)")
        
        return working_companies
    
    def discover_lever_companies(self) -> List[str]:
        """Discover all active Lever companies."""
        self.logger.info("Discovering Lever companies...")
        
        # Lever uses a different URL pattern: https://jobs.lever.co/{company}
        # We'll test common tech companies
        lever_candidates = [
            'netflix', 'uber', 'github', 'shopify', 'slack', 'atlassian',
            'postmates', 'flexport', 'benchling', 'allbirds', 'carta',
            'discord', 'figma', 'notion', 'linear', 'retool', 'vercel',
            'anthropic', 'openai', 'scale', 'nuro', 'cruise', 'waymo'
        ]
        
        working_companies = []
        
        def test_lever_company(company):
            try:
                url = f"https://jobs.lever.co/{company}"
                response = requests.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'jobs' in response.text.lower():
                    # Try to get job count from the API
                    api_url = f"https://api.lever.co/v0/postings/{company}"
                    api_response = requests.get(api_url, timeout=10)
                    if api_response.status_code == 200:
                        jobs_data = api_response.json()
                        if isinstance(jobs_data, list) and len(jobs_data) > 0:
                            return {
                                'company': company,
                                'job_count': len(jobs_data),
                                'has_content': len(jobs_data[0].get('text', '')) > 100
                            }
                return None
            except Exception as e:
                return None
        
        # Test Lever companies in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_company = {executor.submit(test_lever_company, company): company for company in lever_candidates}
            
            for future in as_completed(future_to_company):
                result = future.result()
                if result:
                    working_companies.append(result)
                    self.logger.info(f"✅ Found Lever: {result['company']} ({result['job_count']} jobs)")
        
        return working_companies
    
    def discover_all_companies(self, force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """Discover all available companies from both Lever and Greenhouse."""
        # Check cache first unless forced refresh
        if not force_refresh:
            cached_data = self.load_cached_companies()
            if cached_data and 'greenhouse' in cached_data and 'lever' in cached_data:
                return {
                    'greenhouse': cached_data['greenhouse'],
                    'lever': cached_data['lever']
                }
        
        self.logger.info("Starting comprehensive job board discovery...")
        
        # Discover companies from both platforms
        greenhouse_companies = self.discover_greenhouse_companies()
        lever_companies = self.discover_lever_companies()
        
        companies_data = {
            'greenhouse': greenhouse_companies,
            'lever': lever_companies
        }
        
        # Cache results
        self.save_cached_companies(companies_data)
        
        total_greenhouse_jobs = sum(c['job_count'] for c in greenhouse_companies)
        total_lever_jobs = sum(c['job_count'] for c in lever_companies)
        
        self.logger.info(f"Discovery complete:")
        self.logger.info(f"  Greenhouse: {len(greenhouse_companies)} companies, {total_greenhouse_jobs} jobs")
        self.logger.info(f"  Lever: {len(lever_companies)} companies, {total_lever_jobs} jobs")
        
        return companies_data
    
    def get_company_names_for_greenhouse(self) -> List[str]:
        """Get list of active Greenhouse company names."""
        companies = self.discover_all_companies()
        return [c['company'] for c in companies['greenhouse']]
    
    def get_company_names_for_lever(self) -> List[str]:
        """Get list of active Lever company names."""
        companies = self.discover_all_companies()
        return [c['company'] for c in companies['lever']]