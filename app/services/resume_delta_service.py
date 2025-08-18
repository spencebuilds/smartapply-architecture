"""
SmartApply Rev A Resume Delta Service
Generates deltas against master_bullets with optimization tracking.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import Client


class ResumeDeltaService:
    """Handles resume optimization through delta generation."""
    
    def __init__(self, sb: Client):
        """Initialize with Supabase client."""
        self.sb = sb
        self.logger = logging.getLogger(__name__)
    
    def get_master_bullets(self, user_id: str, master_resume_id: str) -> List[Dict[str, Any]]:
        """Get all master bullets for a resume."""
        try:
            result = self.sb.table("master_bullets").select("*").eq(
                "user_id", user_id
            ).eq(
                "master_resume_id", master_resume_id
            ).order("priority_score", desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting master bullets: {str(e)}")
            return []
    
    def create_resume_optimization(
        self, 
        user_id: str, 
        master_resume_id: str, 
        job_posting_id: str,
        optimized_content: str,
        changes_summary: str,
        optimization_strategy: str,
        fit_improvement: float = 0.0
    ) -> Optional[str]:
        """Create a new resume optimization record."""
        try:
            optimization_data = {
                "user_id": user_id,
                "master_resume_id": master_resume_id,
                "job_posting_id": job_posting_id,
                "optimized_content": optimized_content,
                "changes_summary": changes_summary,
                "optimization_strategy": optimization_strategy,
                "fit_improvement": fit_improvement
            }
            
            result = self.sb.table("resume_optimizations").insert(optimization_data).execute()
            
            if result.data:
                optimization_id = result.data[0]["id"]
                self.logger.info(f"Created resume optimization {optimization_id}")
                return optimization_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating resume optimization: {str(e)}")
            return None
    
    def generate_deltas(
        self, 
        user_id: str,
        optimization_id: str,
        original_bullets: List[Dict[str, Any]],
        optimized_bullets: List[Dict[str, Any]],
        applied_terms: List[str] = None
    ) -> List[str]:
        """
        Generate resume deltas based on bullet point changes.
        Only allows: rephrase, reorder, emphasize, omit operations.
        Blocks creation of new "experience" bullets.
        """
        try:
            delta_ids = []
            applied_terms = applied_terms or []
            
            # Create mapping of original bullets by ID or content
            original_map = {bullet["id"]: bullet for bullet in original_bullets}
            original_content_map = {bullet["bullet_text"]: bullet for bullet in original_bullets}
            
            # Track which original bullets were used
            used_original_ids = set()
            
            # Process optimized bullets
            for opt_bullet in optimized_bullets:
                opt_text = opt_bullet.get("bullet_text", "")
                opt_section = opt_bullet.get("section_name", "")
                
                # Block creation of new experience bullets
                if opt_section.lower() in ["experience", "work experience", "professional experience"]:
                    # Check if this is a completely new bullet (not based on existing)
                    is_new_experience = True
                    original_bullet = None
                    
                    # Try to find matching original bullet
                    for orig_id, orig_bullet in original_map.items():
                        if orig_id in used_original_ids:
                            continue
                        
                        orig_text = orig_bullet.get("bullet_text", "")
                        
                        # Check for similarity (simple word overlap check)
                        if self._bullets_similar(opt_text, orig_text):
                            is_new_experience = False
                            original_bullet = orig_bullet
                            used_original_ids.add(orig_id)
                            break
                    
                    # Block if it's a new experience bullet
                    if is_new_experience:
                        self.logger.warning(f"Blocked creation of new experience bullet: {opt_text[:50]}...")
                        continue
                    
                    # Generate delta for modified experience bullet
                    if original_bullet:
                        delta_id = self._create_delta(
                            user_id, optimization_id, "modify", opt_section,
                            original_bullet["bullet_text"], opt_text,
                            f"Rephrased bullet with applied terms: {', '.join(applied_terms)}"
                        )
                        if delta_id:
                            delta_ids.append(delta_id)
                
                else:
                    # Non-experience bullets - allow modifications
                    # Try to find matching original bullet
                    original_bullet = None
                    for orig_id, orig_bullet in original_map.items():
                        if orig_id in used_original_ids:
                            continue
                        
                        if self._bullets_similar(opt_text, orig_bullet.get("bullet_text", "")):
                            original_bullet = orig_bullet
                            used_original_ids.add(orig_id)
                            break
                    
                    if original_bullet:
                        # Modified existing bullet
                        delta_id = self._create_delta(
                            user_id, optimization_id, "modify", opt_section,
                            original_bullet["bullet_text"], opt_text,
                            "Modified bullet for job optimization"
                        )
                    else:
                        # New non-experience bullet (allowed)
                        delta_id = self._create_delta(
                            user_id, optimization_id, "add", opt_section,
                            "", opt_text,
                            "Added new bullet point"
                        )
                    
                    if delta_id:
                        delta_ids.append(delta_id)
            
            # Handle omitted bullets (original bullets not used)
            for orig_id, orig_bullet in original_map.items():
                if orig_id not in used_original_ids:
                    delta_id = self._create_delta(
                        user_id, optimization_id, "remove", orig_bullet.get("section_name", ""),
                        orig_bullet["bullet_text"], "",
                        "Removed bullet to focus on job-relevant content"
                    )
                    if delta_id:
                        delta_ids.append(delta_id)
            
            self.logger.info(f"Generated {len(delta_ids)} deltas for optimization {optimization_id}")
            return delta_ids
            
        except Exception as e:
            self.logger.error(f"Error generating deltas: {str(e)}")
            return []
    
    def _bullets_similar(self, text1: str, text2: str, threshold: float = 0.3) -> bool:
        """Check if two bullet texts are similar based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def _create_delta(
        self, 
        user_id: str, 
        optimization_id: str, 
        change_type: str,
        section_name: str,
        original_content: str,
        new_content: str,
        reasoning: str
    ) -> Optional[str]:
        """Create a resume delta record."""
        try:
            delta_data = {
                "user_id": user_id,
                "optimization_id": optimization_id,
                "change_type": change_type,
                "section_name": section_name,
                "original_content": original_content,
                "new_content": new_content,
                "reasoning": reasoning
            }
            
            result = self.sb.table("resume_deltas").insert(delta_data).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating delta: {str(e)}")
            return None
    
    def get_optimization_deltas(self, optimization_id: str) -> List[Dict[str, Any]]:
        """Get all deltas for a specific optimization."""
        try:
            result = self.sb.table("resume_deltas").select("*").eq(
                "optimization_id", optimization_id
            ).order("created_at").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting optimization deltas: {str(e)}")
            return []
    
    def create_translation_event_mappings(
        self, 
        translation_event_id: str, 
        concept_mapping_ids: List[str],
        mapping_strengths: List[float] = None
    ) -> List[str]:
        """
        Create translation event mappings (replaces array storage with join table).
        """
        try:
            mapping_ids = []
            mapping_strengths = mapping_strengths or [1.0] * len(concept_mapping_ids)
            
            for i, concept_mapping_id in enumerate(concept_mapping_ids):
                mapping_data = {
                    "translation_event_id": translation_event_id,
                    "concept_mapping_id": concept_mapping_id,
                    "mapping_strength": mapping_strengths[i] if i < len(mapping_strengths) else 1.0
                }
                
                result = self.sb.table("translation_event_mappings").insert(mapping_data).execute()
                
                if result.data:
                    mapping_ids.append(result.data[0]["id"])
            
            self.logger.info(f"Created {len(mapping_ids)} translation event mappings")
            return mapping_ids
            
        except Exception as e:
            self.logger.error(f"Error creating translation event mappings: {str(e)}")
            return []