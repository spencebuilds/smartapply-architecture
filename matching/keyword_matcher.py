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
        
        # Remove special characters and extra whitespace
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
    
    def calculate_match_score(self, job_keywords: List[str], profile_keywords: List[str]) -> float:
        """Calculate match score between job keywords and profile keywords."""
        if not job_keywords or not profile_keywords:
            return 0.0
        
        job_set = set(job_keywords)
        profile_set = set(profile_keywords)
        
        # Calculate intersection
        matches = job_set.intersection(profile_set)
        
        # Calculate score as percentage of profile keywords found in job
        score = (len(matches) / len(profile_set)) * 100
        
        # Bonus for exact phrase matches in original text
        job_text = ' '.join(job_keywords)
        phrase_bonus = 0
        
        for keyword in profile_keywords:
            if len(keyword.split()) > 1 and keyword in job_text:
                phrase_bonus += 5  # 5% bonus per exact phrase match
        
        final_score = min(100.0, score + phrase_bonus)
        
        return round(final_score, 2)
    
    def match_job_to_profile(self, job: Dict[str, Any], profile_name: str, profile_keywords: List[str]) -> Dict[str, Any]:
        """Match a job to a specific resume profile."""
        # Extract job content for matching
        job_content = f"{job.get('title', '')} {job.get('description', '')} {job.get('department', '')}"
        job_keywords = self.extract_keywords(job_content)
        
        # Calculate match score
        match_score = self.calculate_match_score(job_keywords, profile_keywords)
        
        # Find specific matched keywords
        job_keyword_set = set(job_keywords)
        profile_keyword_set = set(profile_keywords)
        matched_keywords = list(job_keyword_set.intersection(profile_keyword_set))
        
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
