"""
Keyword matching engine for job descriptions and resume profiles.
"""

import logging
import re
from typing import Dict, List, Any
from matching.resume_profiles import ResumeProfiles


class KeywordMatcher:
    """Engine for matching job descriptions to resume profiles."""
    
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
    
    def match_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Match a job against all resume profiles and return the best match."""
        profiles = self.resume_profiles.get_all_profiles()
        match_results = []
        
        for profile_name, profile_data in profiles.items():
            profile_keywords = profile_data['keywords']
            match_result = self.match_job_to_profile(job, profile_name, profile_keywords)
            match_results.append(match_result)
        
        # Find best match
        best_match = max(match_results, key=lambda x: x['match_score'])
        
        result = {
            'job_id': job['id'],
            'all_matches': match_results,
            'best_resume': best_match['profile_name'],
            'best_match_score': best_match['match_score'],
            'best_matched_keywords': best_match['matched_keywords'],
            'recommendation': self._generate_recommendation(best_match)
        }
        
        self.logger.debug(f"Job {job['id']} best match: {best_match['profile_name']} ({best_match['match_score']}%)")
        
        return result
    
    def _generate_recommendation(self, match_result: Dict[str, Any]) -> str:
        """Generate a recommendation message based on match results."""
        score = match_result['match_score']
        profile = match_result['profile_name']
        matched_count = match_result['matched_keyword_count']
        total_count = match_result['total_profile_keywords']
        
        if score >= 90:
            return f"Excellent match! Use {profile} resume. {matched_count}/{total_count} keywords matched."
        elif score >= 80:
            return f"Good match! Consider using {profile} resume. {matched_count}/{total_count} keywords matched."
        elif score >= 60:
            return f"Moderate match with {profile} resume. {matched_count}/{total_count} keywords matched."
        else:
            return f"Weak match with {profile} resume. Only {matched_count}/{total_count} keywords matched."
