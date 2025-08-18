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
        
        if self.config.USE_AIRTABLE and self.config.AIRTABLE_API_KEY:
            self.base_url = f"https://api.airtable.com/v0/{self.config.AIRTABLE_BASE_ID}/{self.config.AIRTABLE_TABLE_NAME}"
            self.headers = {
                "Authorization": f"Bearer {self.config.AIRTABLE_API_KEY}",
                "Content-Type": "application/json"
            }
            self.enabled = True
        else:
            self.base_url = None
            self.headers = None
            self.enabled = False
            self.logger.info("Airtable integration disabled")
    
    def format_job_record(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Format job data for Airtable storage."""
        match_result = job.get('match_result', {})
        
        record = {
            "fields": {
                "Job ID": job['id'],
                "Job Title": job['title'],
                "Company": job['company'],
                "Location": job.get('location', ''),
                "Department": job.get('department', ''),
                "Description": job.get('description', '')[:1000],  # Truncate for Airtable limits
                "Job URL": job.get('url', ''),
                "Source": job.get('source', '').title(),
                "Recommended Resume": match_result.get('best_resume', ''),
                "Match Score": match_result.get('best_match_score', 0),
                "Date Found": datetime.now().isoformat(),
                "Status": "New",
                "Applied": False
            }
        }
        
        return record
    
    def store_job(self, job: Dict[str, Any]) -> bool:
        """Store job information in Airtable."""
        if not self.enabled:
            self.logger.debug(f"Airtable disabled, skipping job storage for: {job.get('title', 'Unknown')}")
            return True  # Return success to not break workflow
        
        try:
            record = self.format_job_record(job)
            
            response = requests.post(
                self.base_url,
                json=record,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            if response.status_code == 200:
                self.logger.info(f"Successfully stored job in Airtable: {job['id']}")
                return True
            else:
                self.logger.error(f"Failed to store job in Airtable: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error storing job in Airtable: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error storing job in Airtable: {str(e)}")
            return False
    
    def check_job_exists(self, job_id: str) -> bool:
        """Check if a job already exists in Airtable."""
        if not self.enabled:
            return False  # Always return False when disabled (no job exists)
        
        try:
            params = {
                "filterByFormula": f"{{Job ID}} = '{job_id}'"
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
            self.logger.error(f"Error checking job existence in Airtable: {str(e)}")
            return False
    
    def update_job_status(self, job_id: str, status: str, applied: bool = False) -> bool:
        """Update job application status in Airtable."""
        if not self.enabled:
            self.logger.debug(f"Airtable disabled, skipping status update for job: {job_id}")
            return True  # Return success to not break workflow
        
        try:
            # First, find the record
            params = {
                "filterByFormula": f"{{Job ID}} = '{job_id}'"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                self.logger.warning(f"Job not found in Airtable: {job_id}")
                return False
            
            record_id = records[0]["id"]
            
            # Update the record
            update_data = {
                "fields": {
                    "Status": status,
                    "Applied": applied,
                    "Last Updated": datetime.now().isoformat()
                }
            }
            
            update_response = requests.patch(
                f"{self.base_url}/{record_id}",
                json=update_data,
                headers=self.headers,
                timeout=30
            )
            
            update_response.raise_for_status()
            
            self.logger.info(f"Updated job status in Airtable: {job_id} -> {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating job status in Airtable: {str(e)}")
            return False
    
    def store_application(self, application_data: Dict[str, Any]) -> bool:
        """Store job application record in Airtable."""
        if not self.enabled:
            self.logger.debug("Airtable disabled, skipping application storage")
            return True  # Return success to not break workflow
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
                self.logger.info(f"Successfully stored application in Airtable: {application_data.get('Company')} - {application_data.get('Title')}")
                return True
            else:
                self.logger.error(f"Failed to store application in Airtable: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error storing application in Airtable: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error storing application in Airtable: {str(e)}")
            return False
    
    def check_application_exists(self, job_url: str) -> bool:
        """Check if an application with this job URL already exists in Airtable."""
        if not self.enabled:
            return False  # Always return False when disabled (no application exists)
        
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
