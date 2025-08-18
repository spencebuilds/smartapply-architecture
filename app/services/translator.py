"""
SmartApply Rev A Translator Service
Handles concept translation with company-specific styling and Claude fallback.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from supabase import Client


class ConceptTranslator:
    """Translates concepts with company-specific styling and caching."""
    
    def __init__(self, sb: Client, config):
        """Initialize translator with Supabase client and config."""
        self.sb = sb
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache for concept mappings and company styles
        self._mapping_cache = {}
        self._company_style_cache = {}
        self._cache_valid = False
    
    def _refresh_caches(self):
        """Refresh concept mappings and company style caches."""
        try:
            # Get concept mappings
            result = self.sb.table("concept_mappings").select(
                "raw_term, concept_id, confidence_score, concepts(name)"
            ).execute()
            
            self._mapping_cache = {}
            for mapping in result.data:
                raw_term = mapping.get("raw_term", "").strip().lower()
                concept_data = mapping.get("concepts")
                
                if raw_term and concept_data and isinstance(concept_data, dict):
                    concept_name = concept_data.get("name")
                    if concept_name:
                        if raw_term not in self._mapping_cache:
                            self._mapping_cache[raw_term] = []
                        
                        self._mapping_cache[raw_term].append({
                            "concept_name": concept_name,
                            "confidence": mapping.get("confidence_score", 0),
                            "concept_id": mapping.get("concept_id")
                        })
            
            # Get company term styles
            style_result = self.sb.table("company_term_styles").select(
                "company_id, term_pattern, preferred_style, confidence_score, companies(name)"
            ).execute()
            
            self._company_style_cache = {}
            for style in style_result.data:
                company_data = style.get("companies")
                if company_data and isinstance(company_data, dict):
                    company_name = company_data.get("name", "").lower()
                    term_pattern = style.get("term_pattern", "").lower()
                    
                    if company_name not in self._company_style_cache:
                        self._company_style_cache[company_name] = {}
                    
                    self._company_style_cache[company_name][term_pattern] = {
                        "preferred_style": style.get("preferred_style"),
                        "confidence": style.get("confidence_score", 1.0)
                    }
            
            self._cache_valid = True
            self.logger.info(f"Refreshed translator caches: {len(self._mapping_cache)} mappings, {len(self._company_style_cache)} company styles")
            
        except Exception as e:
            self.logger.error(f"Error refreshing translator caches: {str(e)}")
            self._cache_valid = False
    
    def _get_company_styled_term(self, concept_name: str, company_name: Optional[str] = None) -> str:
        """Get company-specific styled term, fall back to concept name."""
        if not company_name or company_name.lower() not in self._company_style_cache:
            return concept_name
        
        company_styles = self._company_style_cache[company_name.lower()]
        
        # Look for exact match first, then partial matches
        concept_lower = concept_name.lower()
        
        # Direct match
        if concept_lower in company_styles:
            return company_styles[concept_lower]["preferred_style"]
        
        # Partial matches (find best match by confidence)
        best_match = None
        best_confidence = 0
        
        for pattern, style_data in company_styles.items():
            if pattern in concept_lower or concept_lower in pattern:
                confidence = style_data["confidence"]
                if confidence > best_confidence:
                    best_match = style_data["preferred_style"]
                    best_confidence = confidence
        
        return best_match if best_match else concept_name
    
    def _check_claude_throttle(self, company_name: str) -> bool:
        """Check if Claude fallback is within daily limits for company."""
        try:
            # Check API calls from last 24 hours for this company
            yesterday = datetime.now() - timedelta(days=1)
            
            result = self.sb.table("api_calls").select("id").eq(
                "service_name", "claude"
            ).gte(
                "created_at", yesterday.isoformat()
            ).ilike(
                "endpoint", f"%{company_name}%"
            ).execute()
            
            call_count = len(result.data) if result.data else 0
            return call_count < self.config.CLAUDE_DAILY_LIMIT_PER_COMPANY
            
        except Exception as e:
            self.logger.error(f"Error checking Claude throttle for {company_name}: {str(e)}")
            return False
    
    def _get_cached_expansion(self, cache_key: str) -> Optional[str]:
        """Get cached LLM expansion if available and not expired."""
        try:
            result = self.sb.table("llm_cache").select(
                "response_content, expires_at"
            ).eq("cache_key", cache_key).execute()
            
            if result.data:
                cache_entry = result.data[0]
                expires_at = datetime.fromisoformat(cache_entry["expires_at"].replace('Z', '+00:00'))
                
                if expires_at > datetime.now():
                    # Update last_accessed
                    self.sb.table("llm_cache").update({
                        "last_accessed": datetime.now().isoformat()
                    }).eq("cache_key", cache_key).execute()
                    
                    return cache_entry["response_content"]
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached expansion: {str(e)}")
        
        return None
    
    def _cache_expansion(self, cache_key: str, response_content: str, model_name: str = "claude"):
        """Cache LLM expansion with TTL."""
        try:
            expires_at = datetime.now() + timedelta(days=self.config.LLM_CACHE_TTL_DAYS)
            
            cache_data = {
                "cache_key": cache_key,
                "model_name": model_name,
                "prompt_hash": hashlib.sha256(cache_key.encode()).hexdigest(),
                "response_content": response_content,
                "expires_at": expires_at.isoformat(),
                "last_accessed": datetime.now().isoformat()
            }
            
            # Insert or update cache entry
            self.sb.table("llm_cache").upsert(cache_data).execute()
            
        except Exception as e:
            self.logger.error(f"Error caching expansion: {str(e)}")
    
    def _claude_expand_term(self, term: str, company_name: str, context: str = "") -> Optional[str]:
        """Use Claude to expand/rephrase term for company context."""
        if not self.config.USE_CLAUDE_FALLBACK:
            return None
        
        if not self._check_claude_throttle(company_name):
            self.logger.info(f"Claude throttle limit reached for {company_name}")
            return None
        
        # Create cache key
        cache_key = f"expand_{hashlib.sha256(f'{term}_{company_name}_{context}'.encode()).hexdigest()}"
        
        # Check cache first
        cached_result = self._get_cached_expansion(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Log API call start
            api_call_start = datetime.now()
            
            # Simulate Claude API call (would be real implementation)
            # For now, return a styled version based on company context
            expanded_term = f"{term} (optimized for {company_name})"
            
            # Log API call
            api_call_end = datetime.now()
            response_time_ms = int((api_call_end - api_call_start).total_seconds() * 1000)
            
            self.sb.table("api_calls").insert({
                "service_name": "claude",
                "endpoint": f"/expand_term/{company_name}",
                "method": "POST",
                "status_code": 200,
                "response_time_ms": response_time_ms,
                "request_size_bytes": len(term.encode()),
                "response_size_bytes": len(expanded_term.encode())
            }).execute()
            
            # Cache result
            self._cache_expansion(cache_key, expanded_term)
            
            return expanded_term
            
        except Exception as e:
            self.logger.error(f"Error in Claude expansion for {term}: {str(e)}")
            return None
    
    def translate_concept(self, raw_term: str, company_name: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """
        Translate raw term to styled concept.
        
        Returns:
            {
                "concept_name": str,
                "styled_term": str, 
                "confidence": float,
                "source": str,  # "mapping", "company_style", "claude", "fallback"
                "concept_id": str
            }
        """
        if not self._cache_valid:
            self._refresh_caches()
        
        raw_term_lower = raw_term.strip().lower()
        
        # 1. Look up synonym → concept mapping
        concept_info = None
        if raw_term_lower in self._mapping_cache:
            # Get highest confidence mapping
            mappings = self._mapping_cache[raw_term_lower]
            best_mapping = max(mappings, key=lambda x: x["confidence"])
            concept_info = best_mapping
        
        if not concept_info:
            # No mapping found - return raw term
            return {
                "concept_name": raw_term,
                "styled_term": raw_term,
                "confidence": 0.1,
                "source": "fallback",
                "concept_id": None
            }
        
        concept_name = concept_info["concept_name"]
        
        # 2. Apply company-specific styling
        styled_term = self._get_company_styled_term(concept_name, company_name)
        source = "company_style" if styled_term != concept_name else "mapping"
        
        # 3. Claude fallback if enabled and no company styling found
        if styled_term == concept_name and company_name and self.config.USE_CLAUDE_FALLBACK:
            claude_term = self._claude_expand_term(raw_term, company_name, context)
            if claude_term:
                styled_term = claude_term
                source = "claude"
        
        return {
            "concept_name": concept_name,
            "styled_term": styled_term,
            "confidence": concept_info["confidence"],
            "source": source,
            "concept_id": concept_info["concept_id"]
        }
    
    def translate_multiple(self, terms: List[str], company_name: Optional[str] = None, context: str = "") -> List[Dict[str, Any]]:
        """Translate multiple terms efficiently."""
        return [self.translate_concept(term, company_name, context) for term in terms]