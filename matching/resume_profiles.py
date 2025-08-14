"""
Resume profiles with keyword sets for job matching.
"""

import os
import json
import logging
from typing import Dict, List, Any


class ResumeProfiles:
    """Manages resume profiles and their associated keywords."""
    
    def __init__(self):
        """Initialize resume profiles."""
        self.logger = logging.getLogger(__name__)
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict[str, Any]:
        """Load resume profiles from environment or use defaults."""
        # Try to load from environment variable (JSON format)
        profiles_json = os.getenv("RESUME_PROFILES")
        
        if profiles_json:
            try:
                return json.loads(profiles_json)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing RESUME_PROFILES JSON: {str(e)}")
                self.logger.info("Using default resume profiles")
        
        # Default profiles if not provided via environment
        return self._get_default_profiles()
    
    def _get_default_profiles(self) -> Dict[str, Any]:
        """Get default resume profiles with keyword sets."""
        return {
            "Resume_A_Platform_Infrastructure": {
                "keywords": [
                    "platform", "infrastructure", "microservices", "api", "scalability", "aws", "kubernetes",
                    "data", "analytics", "technical product", "cloud", "ci/cd", "observability", "cross-functional"
                ],
                "description": "General Platform Infrastructure focused resume"
            },
            
            "Resume_B_Developer_Tools_Observability": {
                "keywords": [
                    "developer tools", "observability", "devops", "monitoring", "alerting", "instrumentation",
                    "platform engineering", "internal tools", "logging", "on-call", "incident", "runbooks"
                ],
                "description": "Developer Tools & Observability focused resume"
            },
            
            "Resume_C_Billing_Revenue_Platform": {
                "keywords": [
                    "billing", "pricing", "monetization", "payments", "revenue", "invoicing",
                    "payment processor", "checkout", "stripe", "subscription", "fintech", "business model"
                ],
                "description": "Billing & Revenue Platform focused resume"
            }
        }
    
    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """Get a specific resume profile."""
        return self.profiles.get(profile_name, {})
    
    def get_all_profiles(self) -> Dict[str, Any]:
        """Get all resume profiles."""
        return self.profiles
    
    def get_profile_names(self) -> List[str]:
        """Get list of available profile names."""
        return list(self.profiles.keys())
    
    def add_profile(self, name: str, keywords: List[str], description: str = ""):
        """Add a new resume profile."""
        self.profiles[name] = {
            "keywords": keywords,
            "description": description
        }
        self.logger.info(f"Added new resume profile: {name}")
    
    def update_profile_keywords(self, profile_name: str, keywords: List[str]):
        """Update keywords for an existing profile."""
        if profile_name in self.profiles:
            self.profiles[profile_name]["keywords"] = keywords
            self.logger.info(f"Updated keywords for profile: {profile_name}")
        else:
            self.logger.warning(f"Profile not found: {profile_name}")
    
    def remove_profile(self, profile_name: str):
        """Remove a resume profile."""
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            self.logger.info(f"Removed profile: {profile_name}")
        else:
            self.logger.warning(f"Profile not found: {profile_name}")
