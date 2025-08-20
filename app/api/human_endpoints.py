"""
Human-in-the-Loop API endpoints for SmartApply.
No Claude/LLM calls - just data persistence and validation.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import re
import logging

from app.db.supabase_repo import SupabaseRepo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/human", tags=["human-loop"])


# Pydantic Models for Request/Response
class RoleAnalysisRequest(BaseModel):
    """Request model for human role analysis."""
    job_posting_id: str = Field(..., description="UUID of the job posting")
    user_id: str = Field(..., description="UUID of the user")
    analyst_type: str = Field(default="human", description="Always 'human' for this endpoint")
    overall_fit_score: float = Field(..., ge=0, le=100, description="Overall fit score 0-100")
    fit_reasoning: str = Field(..., description="Human's fit assessment reasoning")
    key_matches: Dict[str, str] = Field(default_factory=dict, description="Key matches found")
    vocabulary_gaps: Dict[str, str] = Field(default_factory=dict, description="Vocabulary translation gaps")
    missing_requirements: List[str] = Field(default_factory=list, description="Missing requirements")
    red_flags: str = Field(default="", description="Any red flags identified")
    optimization_strategy: str = Field(..., description="Resume optimization strategy")
    resume_version_recommended: str = Field(..., description="Which resume version to use")
    confidence_level: int = Field(..., ge=1, le=10, description="Confidence level 1-10")
    estimated_application_priority: str = Field(..., description="Application priority (high/medium/low)")


class ResumeDelta(BaseModel):
    """Individual resume bullet change."""
    master_bullet_id: str = Field(..., description="Reference to existing master bullet")
    operation: str = Field(..., description="Operation: rephrase, reorder, emphasize, omit")
    from_text: str = Field(..., description="Original bullet text")
    to_text: Optional[str] = Field(None, description="Modified text (null for omit)")
    concept_ids: List[str] = Field(default_factory=list, description="Concept UUIDs")
    notes: str = Field(default="", description="Notes about the change")


class ResumeOptimizationRequest(BaseModel):
    """Request model for resume optimization."""
    role_analysis_id: str = Field(..., description="UUID from role analysis")
    master_resume_id: str = Field(..., description="UUID of master resume")
    optimization_deltas: Dict[str, Any] = Field(default_factory=dict, description="High-level optimization changes")
    optimization_reasoning: str = Field(..., description="Why these optimizations were made")
    optimized_resume_text: str = Field(..., description="Full optimized resume text")
    optimized_file_url: Optional[str] = Field(None, description="URL to optimized file")
    vocabulary_translations: Dict[str, str] = Field(default_factory=dict, description="Vocabulary mappings used")
    case_studies_highlighted: List[str] = Field(default_factory=list, description="Case study UUIDs highlighted")
    ats_score_estimate: int = Field(..., ge=0, le=100, description="Estimated ATS score")
    human_review_status: str = Field(default="approved", description="Human review status")
    human_review_notes: str = Field(..., description="Human review notes")
    resume_deltas: List[ResumeDelta] = Field(..., description="Individual bullet changes")


class TranslationEventRequest(BaseModel):
    """Request model for translation event logging."""
    application_id: Optional[str] = Field(None, description="Application UUID if applicable")
    role_analysis_id: str = Field(..., description="Role analysis UUID")
    user_id: str = Field(..., description="User UUID")
    event_type: str = Field(default="success", description="Event type")
    original_terms: List[str] = Field(..., description="Original terms found")
    translated_terms: List[str] = Field(..., description="Terms translated to")
    mapping_ids: List[str] = Field(default_factory=list, description="Concept mapping UUIDs used")
    claude_api_used: bool = Field(default=False, description="Always false for human loop")
    api_cost: float = Field(default=0.0, description="Always 0 for human loop")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class ConceptMappingUpsert(BaseModel):
    """Model for creating/updating concept mappings."""
    raw_term: str = Field(..., description="Raw term to map")
    concept_id: str = Field(..., description="Concept UUID")
    company_id: Optional[str] = Field(None, description="Company UUID or null")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    successful_match_count: int = Field(default=0, description="Number of successful matches")
    user_id: str = Field(..., description="User who created mapping")


# Validation Functions
def validate_resume_deltas(deltas: List[ResumeDelta], repo: SupabaseRepo) -> None:
    """Validate resume deltas against business rules."""
    allowed_operations = {'rephrase', 'reorder', 'emphasize', 'omit'}
    
    for delta in deltas:
        # Check operation is allowed
        if delta.operation not in allowed_operations:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid operation '{delta.operation}'. Must be one of: {allowed_operations}"
            )
        
        # Verify master bullet exists
        if not repo.get_master_bullet(delta.master_bullet_id):
            raise HTTPException(
                status_code=400,
                detail=f"Master bullet {delta.master_bullet_id} does not exist"
            )
        
        # Anti-fabrication check: ensure no new metrics/skills added
        if delta.operation == "rephrase" and delta.to_text:
            if _contains_new_metrics_or_skills(delta.from_text, delta.to_text):
                raise HTTPException(
                    status_code=400,
                    detail=f"Resume delta appears to add new metrics or skills not in original text"
                )


def _contains_new_metrics_or_skills(from_text: str, to_text: str) -> bool:
    """Simple check for new numbers or technical skills being added."""
    # Extract numbers from both texts
    from_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', from_text))
    to_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', to_text))
    
    # If new numbers appear, flag as potential fabrication
    if to_numbers - from_numbers:
        return True
    
    # Basic skill keywords check (could be expanded)
    common_skills = {
        'python', 'javascript', 'react', 'typescript', 'sql', 'aws', 'kubernetes', 
        'docker', 'git', 'agile', 'scrum', 'jira', 'confluence', 'figma', 'slack'
    }
    
    from_skills = set(word.lower() for word in from_text.split()) & common_skills
    to_skills = set(word.lower() for word in to_text.split()) & common_skills
    
    # If new technical skills appear, flag as potential fabrication
    if to_skills - from_skills:
        return True
    
    return False


# Dependency to get SupabaseRepo
def get_repo() -> SupabaseRepo:
    """Get Supabase repository instance."""
    try:
        return SupabaseRepo()
    except Exception as e:
        logger.error(f"Failed to initialize Supabase repo: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# API Endpoints
@router.post("/role-analysis")
async def create_role_analysis(
    request: RoleAnalysisRequest,
    repo: SupabaseRepo = Depends(get_repo)
) -> Dict[str, str]:
    """Create a human role analysis."""
    try:
        # Validate UUIDs
        uuid.UUID(request.job_posting_id)
        uuid.UUID(request.user_id)
        
        # Store in role_analyses table
        role_analysis_id = repo.store_role_analysis(
            job_posting_id=request.job_posting_id,
            user_id=request.user_id,
            analyst_type=request.analyst_type,
            overall_fit_score=request.overall_fit_score / 100.0,  # Store as 0-1
            fit_reasoning=request.fit_reasoning,
            key_matches=request.key_matches,
            vocabulary_gaps=request.vocabulary_gaps,
            missing_requirements=request.missing_requirements,
            red_flags=request.red_flags,
            optimization_strategy=request.optimization_strategy,
            resume_version_recommended=request.resume_version_recommended,
            confidence_level=request.confidence_level,
            estimated_application_priority=request.estimated_application_priority
        )
        
        logger.info(f"Created role analysis {role_analysis_id} for job {request.job_posting_id}")
        return {"role_analysis_id": role_analysis_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Error creating role analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role analysis")


@router.post("/resume-optimization")
async def create_resume_optimization(
    request: ResumeOptimizationRequest,
    repo: SupabaseRepo = Depends(get_repo)
) -> Dict[str, str]:
    """Create resume optimization with deltas."""
    try:
        # Validate UUIDs
        uuid.UUID(request.role_analysis_id)
        uuid.UUID(request.master_resume_id)
        
        # Validate resume deltas
        validate_resume_deltas(request.resume_deltas, repo)
        
        # Store resume optimization
        resume_optimization_id = repo.store_resume_optimization(
            role_analysis_id=request.role_analysis_id,
            master_resume_id=request.master_resume_id,
            optimization_deltas=request.optimization_deltas,
            optimization_reasoning=request.optimization_reasoning,
            optimized_resume_text=request.optimized_resume_text,
            optimized_file_url=request.optimized_file_url,
            vocabulary_translations=request.vocabulary_translations,
            case_studies_highlighted=request.case_studies_highlighted,
            ats_score_estimate=request.ats_score_estimate / 100.0,  # Store as 0-1
            human_review_status=request.human_review_status,
            human_review_notes=request.human_review_notes
        )
        
        # Store resume deltas
        for delta in request.resume_deltas:
            repo.store_resume_delta(
                resume_optimization_id=resume_optimization_id,
                master_bullet_id=delta.master_bullet_id,
                operation=delta.operation,
                from_text=delta.from_text,
                to_text=delta.to_text,
                concept_ids=delta.concept_ids,
                notes=delta.notes
            )
        
        logger.info(f"Created resume optimization {resume_optimization_id} with {len(request.resume_deltas)} deltas")
        return {"resume_optimization_id": resume_optimization_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Error creating resume optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create resume optimization")


@router.post("/translation-event")
async def create_translation_event(
    request: TranslationEventRequest,
    mapping_upserts: List[ConceptMappingUpsert] = [],
    repo: SupabaseRepo = Depends(get_repo)
) -> Dict[str, str]:
    """Create translation event with optional mapping upserts."""
    try:
        # Validate UUIDs
        uuid.UUID(request.role_analysis_id)
        uuid.UUID(request.user_id)
        if request.application_id:
            uuid.UUID(request.application_id)
        
        # Upsert any new concept mappings first
        for mapping in mapping_upserts:
            repo.upsert_concept_mapping(
                raw_term=mapping.raw_term,
                concept_id=mapping.concept_id,
                company_id=mapping.company_id,
                confidence_score=mapping.confidence_score,
                successful_match_count=mapping.successful_match_count,
                user_id=mapping.user_id
            )
        
        # Store translation event
        translation_event_id = repo.store_translation_event(
            application_id=request.application_id,
            role_analysis_id=request.role_analysis_id,
            user_id=request.user_id,
            event_type=request.event_type,
            original_terms=request.original_terms,
            translated_terms=request.translated_terms,
            mapping_ids=request.mapping_ids,
            claude_api_used=request.claude_api_used,
            api_cost=request.api_cost,
            processing_time_ms=request.processing_time_ms
        )
        
        logger.info(f"Created translation event {translation_event_id}")
        return {"translation_event_id": translation_event_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    except Exception as e:
        logger.error(f"Error creating translation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create translation event")