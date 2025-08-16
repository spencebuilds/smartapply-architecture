"""
Supabase API client for querying companies and job data.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config import Config


class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Get Supabase credentials from environment variables
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            self.logger.error("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            self.client = None
            return
        
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("Supabase client initialized successfully")
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.client = None
    
    def _test_connection(self):
        """Test the Supabase connection."""
        try:
            if self.client:
                result = self.client.table('companies').select("*").limit(1).execute()
                self.logger.info(f"Supabase connection test successful - Companies table accessible")
        except Exception as e:
            self.logger.warning(f"Supabase connection test failed: {str(e)}")
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Fetch all companies from Supabase."""
        try:
            if not self.client:
                self.logger.error("Supabase client not initialized")
                return []
            
            result = self.client.table('companies').select("*").execute()
            
            if result.data:
                self.logger.info(f"Retrieved {len(result.data)} companies from Supabase")
                return result.data
            else:
                self.logger.warning("No companies found in Supabase")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching companies from Supabase: {str(e)}")
            return []
    
    def get_companies_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Fetch companies that have a specific worldview tag."""
        try:
            if not self.client:
                self.logger.error("Supabase client not initialized")
                return []
            
            # Query companies where the worldview_tags array contains the specified tag
            result = self.client.table('companies').select("*").contains('worldview_tags', [tag]).execute()
            
            if result.data:
                self.logger.info(f"Retrieved {len(result.data)} companies with tag '{tag}' from Supabase")
                return result.data
            else:
                self.logger.info(f"No companies found with tag '{tag}'")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching companies with tag '{tag}' from Supabase: {str(e)}")
            return []
    
    def get_company_names_for_job_fetching(self) -> List[str]:
        """Get company names formatted for job board API calls."""
        try:
            companies = self.get_all_companies()
            
            # Extract company names and format them for API calls
            company_names = []
            for company in companies:
                name = company.get('name', '')
                if name:
                    # Convert to lowercase and replace spaces with hyphens for API compatibility
                    formatted_name = name.lower().replace(' ', '').replace('-', '')
                    company_names.append(formatted_name)
            
            self.logger.info(f"Retrieved {len(company_names)} company names for job fetching")
            return company_names
            
        except Exception as e:
            self.logger.error(f"Error formatting company names: {str(e)}")
            return []
    
    def add_company(self, name: str, worldview_tags: Optional[List[str]] = None, language_patterns: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """Add a new company to the database."""
        try:
            if not self.client:
                self.logger.error("Supabase client not initialized")
                return False
            
            company_data = {
                'name': name,
                'worldview_tags': worldview_tags or [],
                'language_patterns': language_patterns or {},
                **kwargs
            }
            
            result = self.client.table('companies').insert(company_data).execute()
            
            if result.data:
                self.logger.info(f"Successfully added company: {name}")
                return True
            else:
                self.logger.error(f"Failed to add company: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding company {name}: {str(e)}")
            return False
    
    def update_company(self, company_id: int, **updates) -> bool:
        """Update an existing company record."""
        try:
            if not self.client:
                self.logger.error("Supabase client not initialized")
                return False
            
            result = self.client.table('companies').update(updates).eq('id', company_id).execute()
            
            if result.data:
                self.logger.info(f"Successfully updated company ID: {company_id}")
                return True
            else:
                self.logger.error(f"Failed to update company ID: {company_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating company {company_id}: {str(e)}")
            return False
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search companies by name."""
        try:
            if not self.client:
                self.logger.error("Supabase client not initialized")
                return []
            
            # Search in name field using case-insensitive like
            result = self.client.table('companies').select("*").ilike('name', f'%{search_term}%').execute()
            
            if result.data:
                self.logger.info(f"Found {len(result.data)} companies matching '{search_term}'")
                return result.data
            else:
                self.logger.info(f"No companies found matching '{search_term}'")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching companies for '{search_term}': {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the companies database."""
        try:
            if not self.client:
                return {"error": "Supabase client not initialized"}
            
            # Get total count
            total_result = self.client.table('companies').select("*").execute()
            total_companies = len(total_result.data)
            
            # Get count by worldview tags (as examples)
            gaming_result = self.client.table('companies').select("*").contains('worldview_tags', ['gaming-first']).execute()
            gaming_count = len(gaming_result.data)
            
            creator_result = self.client.table('companies').select("*").contains('worldview_tags', ['creator-ecosystem']).execute()
            creator_count = len(creator_result.data)
            
            return {
                "total_companies": total_companies,
                "gaming_companies": gaming_count,
                "creator_ecosystem_companies": creator_count,
                "database_url": self.supabase_url
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}