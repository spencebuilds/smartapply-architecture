"""
Concept extraction service for job descriptions.
Extracts concepts from text using learned mappings and confidence scores.
"""

import re
import logging
from typing import List, Set, Optional
from supabase import Client


class ConceptExtractor:
    """Extracts concepts from job descriptions using learned mappings."""
    
    def __init__(self, sb: Client):
        """Initialize concept extractor with Supabase client."""
        self.sb = sb
        self.logger = logging.getLogger(__name__)
        
        # Cache for concept mappings to avoid repeated queries
        self._mapping_cache = {}
        self._cache_valid = False
    
    def _refresh_mapping_cache(self):
        """Refresh the concept mapping cache."""
        try:
            # Get all concept mappings with concept names
            result = self.sb.table("concept_mappings").select(
                "raw_term, concept_id, confidence_score, concepts(name)"
            ).execute()
            
            self._mapping_cache = {}
            
            for mapping in result.data:
                raw_term = mapping.get("raw_term", "").strip().lower()
                confidence = mapping.get("confidence_score", 0)
                concept_data = mapping.get("concepts")
                
                if raw_term and concept_data and isinstance(concept_data, dict):
                    concept_name = concept_data.get("name")
                    if concept_name:
                        if raw_term not in self._mapping_cache:
                            self._mapping_cache[raw_term] = []
                        
                        self._mapping_cache[raw_term].append({
                            "concept_name": concept_name,
                            "confidence": confidence,
                            "mapping_id": mapping.get("id")
                        })
            
            self._cache_valid = True
            self.logger.info(f"Refreshed concept mapping cache with {len(self._mapping_cache)} terms")
            
        except Exception as e:
            self.logger.error(f"Error refreshing mapping cache: {str(e)}")
            self._cache_valid = False
    
    def extract(self, text: str, company_id: Optional[str] = None) -> List[str]:
        """
        Extract concepts from text using learned mappings.
        
        Args:
            text: The text to analyze (usually job description)
            company_id: Optional company ID for company-specific mappings
            
        Returns:
            List of extracted concept names
        """
        if not text:
            return []
        
        # Refresh cache if needed
        if not self._cache_valid:
            self._refresh_mapping_cache()
        
        if not self._mapping_cache:
            self.logger.warning("No concept mappings available")
            return []
        
        extracted_concepts: Set[str] = set()
        low_confidence_terms: Set[str] = set()
        
        # Normalize text for matching
        normalized_text = text.lower()
        
        # Match against cached mappings
        for raw_term, mappings in self._mapping_cache.items():
            # Use word boundary regex for better matching
            pattern = rf"\b{re.escape(raw_term)}\b"
            
            if re.search(pattern, normalized_text, flags=re.IGNORECASE):
                # Get the best mapping for this term
                best_mapping = max(mappings, key=lambda m: m["confidence"])
                
                if best_mapping["confidence"] >= 0.7:
                    extracted_concepts.add(best_mapping["concept_name"])
                    self.logger.debug(f"High confidence match: '{raw_term}' -> '{best_mapping['concept_name']}'")
                else:
                    low_confidence_terms.add(raw_term)
                    self.logger.debug(f"Low confidence match: '{raw_term}' (confidence: {best_mapping['confidence']})")
        
        # Log low confidence terms for potential review
        if low_confidence_terms:
            self.logger.info(f"Found {len(low_confidence_terms)} low confidence terms: {list(low_confidence_terms)[:5]}")
        
        result = list(extracted_concepts)
        self.logger.info(f"Extracted {len(result)} concepts from text")
        return result
    
    def extract_with_confidence(self, text: str, company_id: Optional[str] = None) -> List[dict]:
        """
        Extract concepts with confidence scores.
        
        Returns:
            List of dicts with 'concept', 'confidence', and 'raw_term' keys
        """
        if not text:
            return []
        
        if not self._cache_valid:
            self._refresh_mapping_cache()
        
        if not self._mapping_cache:
            return []
        
        results = []
        normalized_text = text.lower()
        
        for raw_term, mappings in self._mapping_cache.items():
            pattern = rf"\b{re.escape(raw_term)}\b"
            
            if re.search(pattern, normalized_text, flags=re.IGNORECASE):
                best_mapping = max(mappings, key=lambda m: m["confidence"])
                
                results.append({
                    "concept": best_mapping["concept_name"],
                    "confidence": best_mapping["confidence"],
                    "raw_term": raw_term,
                    "mapping_id": best_mapping["mapping_id"]
                })
        
        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results
    
    def add_manual_mapping(self, raw_term: str, concept_name: str, 
                          confidence_score: float = 0.8) -> bool:
        """
        Manually add a concept mapping.
        
        Args:
            raw_term: The raw term from job descriptions
            concept_name: The concept it maps to
            confidence_score: Confidence in this mapping (0.0 to 1.0)
            
        Returns:
            True if successful
        """
        try:
            # Get or create the concept
            concept_result = self.sb.table("concepts").select("id").eq("name", concept_name).execute()
            
            if concept_result.data:
                concept_id = concept_result.data[0]["id"]
            else:
                # Create new concept
                create_result = self.sb.table("concepts").insert({"name": concept_name}).execute()
                if not create_result.data:
                    self.logger.error(f"Failed to create concept: {concept_name}")
                    return False
                concept_id = create_result.data[0]["id"]
            
            # Create mapping
            mapping_data = {
                "raw_term": raw_term.lower().strip(),
                "concept_id": concept_id,
                "confidence_score": confidence_score
            }
            
            result = self.sb.table("concept_mappings").insert(mapping_data).execute()
            
            if result.data:
                self.logger.info(f"Added manual mapping: '{raw_term}' -> '{concept_name}' (confidence: {confidence_score})")
                # Invalidate cache to force refresh
                self._cache_valid = False
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding manual mapping: {str(e)}")
            return False
    
    def get_mapping_stats(self) -> dict:
        """Get statistics about concept mappings."""
        try:
            if not self._cache_valid:
                self._refresh_mapping_cache()
            
            total_mappings = sum(len(mappings) for mappings in self._mapping_cache.values())
            unique_terms = len(self._mapping_cache)
            
            # Calculate confidence distribution
            all_confidences = []
            for mappings in self._mapping_cache.values():
                for mapping in mappings:
                    all_confidences.append(mapping["confidence"])
            
            high_confidence = len([c for c in all_confidences if c >= 0.7])
            medium_confidence = len([c for c in all_confidences if 0.3 <= c < 0.7])
            low_confidence = len([c for c in all_confidences if c < 0.3])
            
            return {
                "total_mappings": total_mappings,
                "unique_terms": unique_terms,
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence,
                "avg_confidence": sum(all_confidences) / len(all_confidences) if all_confidences else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting mapping stats: {str(e)}")
            return {"error": str(e)}