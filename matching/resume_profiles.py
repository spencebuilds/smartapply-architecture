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
            "Software_Engineer": {
                "keywords": [
                    # Programming Languages
                    "python", "javascript", "java", "c++", "c#", "go", "rust", "typescript",
                    "react", "angular", "vue", "node.js", "express", "django", "flask",
                    
                    # Technologies & Frameworks
                    "api", "rest", "graphql", "microservices", "docker", "kubernetes",
                    "aws", "azure", "gcp", "cloud", "devops", "ci/cd", "git", "github",
                    
                    # Databases
                    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
                    
                    # Concepts
                    "software development", "full stack", "backend", "frontend",
                    "system design", "architecture", "scalability", "performance",
                    "testing", "unit testing", "integration testing", "agile", "scrum"
                ],
                "description": "Software engineering and development focused resume"
            },
            
            "Data_Scientist": {
                "keywords": [
                    # Programming & Tools
                    "python", "r", "sql", "jupyter", "pandas", "numpy", "scikit-learn",
                    "tensorflow", "pytorch", "keras", "scipy", "matplotlib", "seaborn",
                    
                    # Data Science Concepts
                    "machine learning", "deep learning", "artificial intelligence",
                    "data analysis", "statistical analysis", "predictive modeling",
                    "feature engineering", "model validation", "cross-validation",
                    
                    # Statistics & Math
                    "statistics", "probability", "regression", "classification",
                    "clustering", "time series", "hypothesis testing", "a/b testing",
                    
                    # Big Data & Cloud
                    "big data", "spark", "hadoop", "databricks", "snowflake",
                    "aws", "azure", "gcp", "tableau", "power bi", "looker",
                    
                    # Business
                    "data visualization", "business intelligence", "analytics",
                    "insights", "kpi", "metrics", "reporting", "dashboard"
                ],
                "description": "Data science and analytics focused resume"
            },
            
            "Product_Manager": {
                "keywords": [
                    # Product Management
                    "product management", "product strategy", "product roadmap",
                    "product development", "feature prioritization", "user stories",
                    "requirements gathering", "stakeholder management",
                    
                    # Business & Strategy
                    "business strategy", "market research", "competitive analysis",
                    "go-to-market", "pricing strategy", "business metrics", "kpi",
                    "roi", "revenue", "growth", "market analysis",
                    
                    # User Experience
                    "user experience", "ux", "ui", "user research", "customer feedback",
                    "user testing", "personas", "customer journey", "wireframes",
                    
                    # Project Management
                    "agile", "scrum", "kanban", "jira", "confluence", "project management",
                    "cross-functional teams", "leadership", "communication",
                    
                    # Analytics & Data
                    "analytics", "data analysis", "metrics", "a/b testing",
                    "user analytics", "product analytics", "sql", "tableau",
                    "google analytics", "mixpanel", "amplitude",
                    
                    # Technical Understanding
                    "api", "technical specifications", "system architecture",
                    "mobile", "web", "saas", "platform", "integration"
                ],
                "description": "Product management and strategy focused resume"
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
