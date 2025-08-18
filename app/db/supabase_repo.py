"""
Comprehensive Supabase repository layer for the job application system.
Handles all database operations with proper error handling and logging.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client


class SupabaseRepo:
    """Repository layer for all Supabase database operations."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """Initialize Supabase repository."""
        self.logger = logging.getLogger(__name__)
        
        # Get credentials from environment or parameters
        self.supabase_url = url or os.getenv("SUPABASE_URL")
        self.supabase_key = key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            self.logger.error("SUPABASE_URL and SUPABASE_KEY are required")
            raise ValueError("Missing Supabase credentials")
        
        try:
            self.sb: Client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("Supabase repository initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    # USER OPERATIONS
    def get_or_create_user(self, email: str, **kwargs) -> str:
        """Get existing user or create new one. Returns user_id."""
        try:
            # Try to find existing user
            result = self.sb.table("users").select("id").eq("email", email).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new user
            user_data = {"email": email, **kwargs}
            result = self.sb.table("users").insert(user_data).execute()
            
            if result.data:
                self.logger.info(f"Created new user: {email}")
                return result.data[0]["id"]
            
            raise Exception("Failed to create user")
            
        except Exception as e:
            self.logger.error(f"Error getting/creating user {email}: {str(e)}")
            raise
    
    def update_user(self, user_id: str, **updates) -> bool:
        """Update user information."""
        try:
            result = self.sb.table("users").update(updates).eq("id", user_id).execute()
            return bool(result.data)
        except Exception as e:
            self.logger.error(f"Error updating user {user_id}: {str(e)}")
            return False
    
    # COMPANY OPERATIONS
    def get_or_create_company(self, name: str, **kwargs) -> str:
        """Get existing company or create new one. Returns company_id."""
        try:
            # Try to find existing company
            result = self.sb.table("companies").select("id").eq("name", name).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new company
            company_data = {"name": name, **kwargs}
            result = self.sb.table("companies").insert(company_data).execute()
            
            if result.data:
                self.logger.info(f"Created new company: {name}")
                return result.data[0]["id"]
            
            raise Exception("Failed to create company")
            
        except Exception as e:
            self.logger.error(f"Error getting/creating company {name}: {str(e)}")
            raise
    
    def get_companies_for_job_fetching(self) -> List[str]:
        """Get list of company names for job fetching APIs."""
        try:
            result = self.sb.table("companies").select("name").execute()
            
            if result.data:
                company_names = []
                for company in result.data:
                    name = company.get('name', '')
                    if name:
                        # Format for API compatibility
                        formatted_name = name.lower().replace(' ', '').replace('-', '')
                        company_names.append(formatted_name)
                
                self.logger.info(f"Retrieved {len(company_names)} companies for job fetching")
                return company_names
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching companies: {str(e)}")
            return []
    
    # CONCEPT OPERATIONS
    def get_or_create_concept(self, name: str) -> str:
        """Get existing concept or create new one. Returns concept_id."""
        try:
            # Try to find existing concept
            result = self.sb.table("concepts").select("id").eq("name", name).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new concept
            result = self.sb.table("concepts").insert({"name": name}).execute()
            
            if result.data:
                self.logger.info(f"Created new concept: {name}")
                return result.data[0]["id"]
            
            raise Exception("Failed to create concept")
            
        except Exception as e:
            self.logger.error(f"Error getting/creating concept {name}: {str(e)}")
            raise
    
    def get_or_create_concept_mapping(self, raw_term: str, concept_name: str, 
                                    confidence_score: float = 0.5, 
                                    user_id: Optional[str] = None,
                                    company_id: Optional[str] = None) -> str:
        """Get or create concept mapping. Returns mapping_id."""
        try:
            # Get concept_id
            concept_id = self.get_or_create_concept(concept_name)
            
            # Try to find existing mapping
            result = self.sb.table("concept_mappings").select("id").eq("raw_term", raw_term).eq("concept_id", concept_id).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new mapping
            mapping_data = {
                "raw_term": raw_term,
                "concept_id": concept_id,
                "confidence_score": confidence_score,
                "user_id": user_id,
                "company_id": company_id
            }
            
            result = self.sb.table("concept_mappings").insert(mapping_data).execute()
            
            if result.data:
                self.logger.info(f"Created concept mapping: {raw_term} -> {concept_name}")
                return result.data[0]["id"]
            
            raise Exception("Failed to create concept mapping")
            
        except Exception as e:
            self.logger.error(f"Error creating concept mapping {raw_term}: {str(e)}")
            raise
    
    # JOB POSTING OPERATIONS
    def store_job_posting(self, company_name: str, role_title: str, job_url: str,
                         job_description: str, extracted_concepts: List[str] = None,
                         posted_at: Optional[datetime] = None) -> str:
        """Store job posting. Returns job_posting_id."""
        try:
            # Get or create company
            company_id = None
            if company_name:
                try:
                    company_id = self.get_or_create_company(company_name)
                except Exception as e:
                    self.logger.warning(f"Could not create company {company_name}: {e}")
            
            # Check if job already exists
            result = self.sb.table("job_postings").select("id").eq("job_url", job_url).execute()
            
            if result.data:
                # Update existing job
                job_id = result.data[0]["id"]
                updates = {
                    "job_description": job_description,
                    "extracted_concepts": extracted_concepts or [],
                    "updated_at": datetime.now().isoformat()
                }
                self.sb.table("job_postings").update(updates).eq("id", job_id).execute()
                return job_id
            
            # Create new job posting
            job_data = {
                "company_name": company_name,
                "role_title": role_title,
                "job_url": job_url,
                "job_description": job_description,
                "company_id": company_id,
                "extracted_concepts": extracted_concepts or [],
                "posted_at": posted_at.isoformat() if posted_at else None
            }
            
            result = self.sb.table("job_postings").insert(job_data).execute()
            
            if result.data:
                job_id = result.data[0]["id"]
                self.logger.info(f"Stored job posting: {role_title} at {company_name}")
                return job_id
            
            raise Exception("Failed to store job posting")
            
        except Exception as e:
            self.logger.error(f"Error storing job posting {job_url}: {str(e)}")
            raise
    
    def store_job_analysis(self, company_name: str, role_title: str, job_url: str,
                          job_description: str, fit_score: float, reasoning: str,
                          vocabulary_gaps: List[str] = None,
                          optimization_strategy: str = None) -> str:
        """Store job posting and analysis. Returns analysis_id."""
        try:
            # Store job posting first
            job_posting_id = self.store_job_posting(
                company_name=company_name,
                role_title=role_title,
                job_url=job_url,
                job_description=job_description
            )
            
            # Store role analysis
            analysis_data = {
                "job_posting_id": job_posting_id,
                "fit_score": fit_score,
                "reasoning": reasoning,
                "vocabulary_gaps": vocabulary_gaps or [],
                "optimization_strategy": optimization_strategy
            }
            
            result = self.sb.table("role_analysis").insert(analysis_data).execute()
            
            if result.data:
                analysis_id = result.data[0]["id"]
                self.logger.info(f"Stored job analysis for {role_title}: fit_score={fit_score}")
                return analysis_id
            
            raise Exception("Failed to store job analysis")
            
        except Exception as e:
            self.logger.error(f"Error storing job analysis for {job_url}: {str(e)}")
            raise
    
    # APPLICATION OPERATIONS
    def upsert_application(self, user_id: str, job_posting_id: str, 
                          resume_id: Optional[str] = None, status: str = "applied",
                          feedback: Optional[str] = None) -> str:
        """Create or update application. Returns application_id."""
        try:
            # Check for existing application
            result = self.sb.table("applications").select("id").eq("user_id", user_id).eq("job_posting_id", job_posting_id).execute()
            
            if result.data:
                # Update existing application
                app_id = result.data[0]["id"]
                updates = {
                    "status": status,
                    "feedback": feedback,
                    "updated_at": datetime.now().isoformat()
                }
                self.sb.table("applications").update(updates).eq("id", app_id).execute()
                self.logger.info(f"Updated application {app_id}: status={status}")
                return app_id
            
            # Create new application
            app_data = {
                "user_id": user_id,
                "job_posting_id": job_posting_id,
                "resume_id": resume_id,
                "status": status,
                "feedback": feedback,
                "submitted_at": datetime.now().isoformat()
            }
            
            result = self.sb.table("applications").insert(app_data).execute()
            
            if result.data:
                app_id = result.data[0]["id"]
                self.logger.info(f"Created application {app_id}: status={status}")
                return app_id
            
            raise Exception("Failed to create application")
            
        except Exception as e:
            self.logger.error(f"Error upserting application: {str(e)}")
            raise
    
    # LEARNING/TRANSLATION OPERATIONS
    def record_translation_event(self, concept_mapping_id: str, application_id: str,
                                event_type: str = "success") -> str:
        """Record a translation learning event. Returns event_id."""
        try:
            event_data = {
                "concept_mapping_id": concept_mapping_id,
                "application_id": application_id,
                "event_type": event_type
            }
            
            result = self.sb.table("translation_events").insert(event_data).execute()
            
            if result.data:
                event_id = result.data[0]["id"]
                
                # Increment successful_match_count for the concept mapping
                if event_type == "success":
                    self.sb.table("concept_mappings").rpc(
                        "increment_match_count",
                        {"mapping_id": concept_mapping_id}
                    ).execute()
                
                self.logger.info(f"Recorded translation event: {event_type}")
                return event_id
            
            raise Exception("Failed to record translation event")
            
        except Exception as e:
            self.logger.error(f"Error recording translation event: {str(e)}")
            raise
    
    def increment_concept_mapping_success(self, concept_mapping_id: str) -> bool:
        """Increment successful match count for a concept mapping."""
        try:
            # Get current count
            result = self.sb.table("concept_mappings").select("successful_match_count").eq("id", concept_mapping_id).execute()
            
            if not result.data:
                return False
            
            current_count = result.data[0].get("successful_match_count", 0)
            new_count = (current_count or 0) + 1
            
            # Update count
            self.sb.table("concept_mappings").update({"successful_match_count": new_count}).eq("id", concept_mapping_id).execute()
            
            self.logger.info(f"Incremented concept mapping success count to {new_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error incrementing concept mapping success: {str(e)}")
            return False
    
    # ANALYTICS OPERATIONS
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            stats = {}
            
            # Count records in each table
            tables = ["users", "companies", "concepts", "job_postings", "applications", "concept_mappings", "translation_events"]
            
            for table in tables:
                try:
                    result = self.sb.table(table).select("*", count="exact").execute()
                    stats[f"{table}_count"] = result.count if hasattr(result, 'count') else len(result.data)
                except Exception as e:
                    stats[f"{table}_count"] = f"Error: {str(e)}"
            
            # Additional analytics
            try:
                # Average fit scores
                result = self.sb.table("role_analysis").select("fit_score").execute()
                if result.data:
                    scores = [r.get("fit_score", 0) for r in result.data if r.get("fit_score") is not None]
                    stats["avg_fit_score"] = sum(scores) / len(scores) if scores else 0
                
                # Top concepts by usage
                result = self.sb.table("concept_mappings").select("concept_id, successful_match_count").order("successful_match_count", desc=True).limit(5).execute()
                stats["top_concepts"] = result.data
                
            except Exception as e:
                stats["analytics_error"] = str(e)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}