"""
Keyword matching engine for job descriptions and resume profiles.
Now using concept-based grouping algorithm for better matching accuracy.
"""

import logging
import re
from typing import Dict, List, Any
from matching.resume_profiles import ResumeProfiles
from matching.concept_matcher import analyze_job_posting


class KeywordMatcher:
    """Engine for matching job descriptions to resume profiles using concept-based algorithm."""
    
    def __init__(self):
        """Initialize keyword matcher."""
        self.logger = logging.getLogger(__name__)
        self.resume_profiles = ResumeProfiles()
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace common separators with spaces for better keyword matching
        text = re.sub(r'[/\-_]', ' ', text)
        
        # Remove special characters except spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'can', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def calculate_match_score(self, job_text: str, profile_keywords: List[str]) -> float:
        """Calculate match score between job text and profile keywords."""
        if not job_text or not profile_keywords:
            return 0.0
        
        # Clean the job text for matching
        cleaned_job_text = self.clean_text(job_text)
        
        matches = 0
        total_keywords = len(profile_keywords)
        
        # Check each profile keyword against the job text
        for keyword in profile_keywords:
            cleaned_keyword = self.clean_text(keyword)
            
            # Check for exact keyword match in the text
            if cleaned_keyword in cleaned_job_text:
                matches += 1
                continue
            
            # For multi-word keywords, also check if all words are present
            if len(cleaned_keyword.split()) > 1:
                keyword_words = cleaned_keyword.split()
                if all(word in cleaned_job_text for word in keyword_words):
                    matches += 1
        
        # Calculate percentage score
        score = (matches / total_keywords) * 100
        
        return round(score, 2)
    
    def match_job_to_profile(self, job: Dict[str, Any], profile_name: str, profile_keywords: List[str]) -> Dict[str, Any]:
        """Match a job to a specific resume profile."""
        # Extract job content for matching
        job_content = f"{job.get('title', '')} {job.get('description', '')} {job.get('department', '')}"
        
        # Calculate match score using the improved algorithm
        match_score = self.calculate_match_score(job_content, profile_keywords)
        
        # Find specific matched keywords by checking each profile keyword
        matched_keywords = []
        cleaned_job_content = self.clean_text(job_content)
        
        for keyword in profile_keywords:
            cleaned_keyword = self.clean_text(keyword)
            if cleaned_keyword in cleaned_job_content:
                matched_keywords.append(keyword)
            elif len(cleaned_keyword.split()) > 1:
                keyword_words = cleaned_keyword.split()
                if all(word in cleaned_job_content for word in keyword_words):
                    matched_keywords.append(keyword)
        
        return {
            'profile_name': profile_name,
            'match_score': match_score,
            'matched_keywords': matched_keywords,
            'total_profile_keywords': len(profile_keywords),
            'matched_keyword_count': len(matched_keywords)
        }
    
    def is_product_manager_role(self, job: Dict[str, Any]) -> bool:
        """Check if a job is a Product Manager role."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        department = job.get('department', '').lower()
        
        # Product Manager keywords in title
        pm_title_keywords = [
            'product manager', 'product lead', 'product owner', 'product director',
            'senior product manager', 'staff product manager', 'principal product manager',
            'group product manager', 'product management', 'pm -', 'product strategy'
        ]
        
        # Check title first (most important)
        for keyword in pm_title_keywords:
            if keyword in title:
                return True
        
        # Check department
        if 'product' in department and any(word in title for word in ['manager', 'lead', 'director', 'owner']):
            return True
        
        return False

    def match_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Match a job against all resume profiles using concept-based algorithm."""
        # First check if this is a Product Manager role
        if not self.is_product_manager_role(job):
            # Return a low score result for non-PM roles
            return {
                'job_id': job['id'],
                'all_matches': [],
                'best_resume': 'None',
                'best_match_score': 0.0,
                'best_matched_keywords': [],
                'recommendation': 'Not a Product Manager role - skipped'
            }
        
        # Use the new concept-based matching algorithm
        job_content = f"{job.get('title', '')} {job.get('description', '')}"
        company = job.get('company', 'Unknown')
        
        try:
            analysis_result = analyze_job_posting(job_content, company)
            
            # Convert the concept-based result to the expected format
            best_resume = analysis_result.get('recommended_resume', 'None')
            raw_score = analysis_result.get('match_score', 0)
            
            # Convert raw concept count to percentage (normalize against typical range)
            # Based on testing: good matches typically have 1-4 concept matches, excellent matches have 5+
            normalized_score = min(100.0, (raw_score / 4.0) * 100.0) if raw_score > 0 else 0.0
            
            # Get matched concepts as "keywords" for compatibility
            concept_breakdown = analysis_result.get('concept_breakdown', {})
            matched_concepts = list(concept_breakdown.keys()) if concept_breakdown else []
            
            # Create match results for all resumes for compatibility
            all_resume_scores = analysis_result.get('resume_match_breakdown', {})
            match_results = []
            for resume_name, score in all_resume_scores.items():
                normalized_resume_score = min(100.0, (score / 4.0) * 100.0) if score > 0 else 0.0
                match_results.append({
                    'profile_name': resume_name,
                    'match_score': normalized_resume_score,
                    'matched_keywords': matched_concepts if resume_name == best_resume else [],
                    'total_profile_keywords': 8,  # Approximate concept count
                    'matched_keyword_count': score
                })
            
            result = {
                'job_id': job['id'],
                'all_matches': match_results,
                'best_resume': best_resume,
                'best_match_score': normalized_score,
                'best_matched_keywords': matched_concepts,
                'recommendation': self._generate_recommendation({'match_score': normalized_score, 'profile_name': best_resume}),
                'concept_analysis': analysis_result  # Add full concept analysis for debugging
            }
            
        except Exception as e:
            self.logger.error(f"Error in concept-based matching: {str(e)}")
            # Fallback to simple scoring for PM roles
            result = {
                'job_id': job['id'],
                'all_matches': [],
                'best_resume': 'Resume A',
                'best_match_score': 15.0,  # Minimum threshold for PM roles
                'best_matched_keywords': ['product manager'],
                'recommendation': 'PM role detected - using fallback scoring'
            }
        
        return result
    
    def _generate_recommendation(self, match_result: Dict[str, Any]) -> str:
        """Generate a recommendation message based on match results."""
        score = match_result['match_score']
        profile = match_result['profile_name']
        
        if score >= 90:
            return f"Excellent match! Use {profile} resume."
        elif score >= 80:
            return f"Good match! Consider using {profile} resume."
        elif score >= 60:
            return f"Moderate match with {profile} resume."
        else:
            return f"Weak match with {profile} resume."
