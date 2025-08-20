"""
Translator Service - Sanitized Demo Version
Portfolio showcase of vocabulary translation architecture.
Production version contains proprietary mapping algorithms.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TranslatorService:
    """
    Demo stub: Vocabulary translation service for company-specific term mapping.
    
    In production, this service:
    - Maps technical terms to company-preferred vocabulary
    - Uses ML models for semantic similarity
    - Maintains company-specific style guides
    - Integrates with LLM fallback for unknown terms
    
    This demo version echoes inputs to avoid exposing proprietary logic.
    """
    
    def __init__(self):
        """Initialize translator with demo mappings."""
        # Demo mappings for showcase purposes
        self.demo_mappings = {
            "api": "application programming interface",
            "microservices": "distributed services architecture",
            "observability": "system monitoring and alerting",
            "developer experience": "engineering productivity",
            "platform": "shared infrastructure services"
        }
        logger.info("TranslatorService initialized (demo mode)")
    
    def translate_term(self, term: str, company: str = None) -> str:
        """
        Translate a single term to company-preferred vocabulary.
        
        Args:
            term: Original term from job posting
            company: Company name for context-specific mapping
            
        Returns:
            Translated term or original if no mapping found
        """
        # Demo logic: simple lookup with fallback
        normalized_term = term.lower().strip()
        
        if normalized_term in self.demo_mappings:
            translated = self.demo_mappings[normalized_term]
            logger.info(f"Demo translation: '{term}' -> '{translated}' for {company}")
            return translated
        
        # In production: would query concept_mappings table with company context
        # For demo: return original term
        return term
    
    def translate_terms(self, terms: List[str], company: str = None) -> List[str]:
        """
        Translate multiple terms with batch optimization.
        
        Args:
            terms: List of terms to translate
            company: Company context for translation
            
        Returns:
            List of translated terms
        """
        return [self.translate_term(term, company) for term in terms]
    
    def get_translation_confidence(self, term: str, company: str = None) -> float:
        """
        Get confidence score for term translation.
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Demo logic: high confidence for known mappings
        if term.lower().strip() in self.demo_mappings:
            return 0.95
        
        # In production: would use ML model confidence scores
        return 0.5
    
    def batch_translate_with_confidence(self, terms: List[str], company: str = None) -> List[Dict[str, any]]:
        """
        Translate terms with confidence scores and metadata.
        
        Returns:
            List of translation results with confidence and source
        """
        results = []
        
        for term in terms:
            translated = self.translate_term(term, company)
            confidence = self.get_translation_confidence(term, company)
            
            results.append({
                "original": term,
                "translated": translated,
                "confidence": confidence,
                "source": "demo_mapping" if confidence > 0.9 else "passthrough",
                "company_context": company
            })
        
        return results
    
    def learn_from_feedback(self, original: str, preferred: str, company: str = None) -> bool:
        """
        Learn from human feedback to improve translations.
        
        In production: updates concept_mappings table and retrains models.
        Demo version: logs feedback for showcase.
        """
        logger.info(f"Learning feedback: '{original}' -> '{preferred}' for {company}")
        
        # In production: would update database and trigger model retraining
        return True
    
    def get_company_style_guide(self, company: str) -> Dict[str, str]:
        """
        Get company-specific terminology preferences.
        
        Returns:
            Dictionary of term preferences for the company
        """
        # Demo company styles
        demo_styles = {
            "stripe": {
                "payment": "financial transaction",
                "merchant": "business customer",
                "api": "developer interface"
            },
            "epic": {
                "game": "interactive experience",
                "player": "user",
                "monetization": "revenue optimization"
            }
        }
        
        return demo_styles.get(company.lower(), {})
    
    def validate_translation_quality(self, original: str, translated: str) -> Dict[str, any]:
        """
        Validate translation quality and detect potential issues.
        
        Returns:
            Validation results with quality score and flags
        """
        # Demo quality checks
        quality_score = 0.8
        flags = []
        
        # Check for length changes
        if len(translated) > len(original) * 2:
            flags.append("excessive_expansion")
            quality_score -= 0.2
        
        # Check for term preservation
        if original.lower() == translated.lower():
            flags.append("no_translation_applied")
        
        return {
            "quality_score": max(0.0, quality_score),
            "flags": flags,
            "passed": quality_score >= 0.6
        }