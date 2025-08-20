"""
SmartApply Architecture Demo API
Portfolio showcase of human-in-the-loop job analysis system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SmartApply Architecture Demo",
    description="Portfolio showcase of human-in-the-loop job analysis system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models (Production API Shapes)

class RoleAnalysis(BaseModel):
    """Human role analysis validation model."""
    job_posting_id: str = Field(..., description="UUID of the job posting")
    user_id: str = Field(..., description="UUID of the user")
    analyst_type: str = Field(default="human", description="Always 'human' for this demo")
    overall_fit_score: int = Field(..., ge=0, le=100, description="Overall fit score 0-100")
    fit_reasoning: str = Field(..., description="Human's fit assessment reasoning")
    key_matches: Dict[str, str] = Field(default_factory=dict, description="Key matches found")
    vocabulary_gaps: Dict[str, str] = Field(default_factory=dict, description="Vocabulary gaps")
    missing_requirements: List[str] = Field(default_factory=list, description="Missing requirements")
    red_flags: Optional[str] = Field(None, description="Any red flags identified")
    optimization_strategy: str = Field(..., description="Resume optimization strategy")
    resume_version_recommended: str = Field(..., description="Which resume version to use")
    confidence_level: int = Field(..., ge=1, le=10, description="Confidence level 1-10")
    estimated_application_priority: str = Field(..., description="Priority (high/medium/low)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


class ResumeDelta(BaseModel):
    """Resume bullet change model."""
    master_bullet_id: str = Field(..., description="Reference to existing master bullet")
    operation: str = Field(..., description="Operation: rephrase, reorder, emphasize, omit")
    from_text: str = Field(..., description="Original bullet text")
    to_text: Optional[str] = Field(None, description="Modified text (null for omit)")
    concept_ids: List[str] = Field(default_factory=list, description="Concept UUIDs")
    notes: str = Field(default="", description="Notes about the change")


class ResumeOptimization(BaseModel):
    """Resume optimization validation model."""
    role_analysis_id: str = Field(..., description="UUID from role analysis")
    master_resume_id: str = Field(..., description="UUID of master resume")
    optimization_deltas: Dict[str, Any] = Field(default_factory=dict, description="High-level changes")
    optimization_reasoning: str = Field(..., description="Why these optimizations were made")
    optimized_resume_text: str = Field(..., description="Full optimized resume text")
    optimized_file_url: Optional[str] = Field(None, description="URL to optimized file")
    vocabulary_translations: Dict[str, str] = Field(default_factory=dict, description="Vocab mappings")
    case_studies_highlighted: List[str] = Field(default_factory=list, description="Case study UUIDs")
    ats_score_estimate: int = Field(..., ge=0, le=100, description="Estimated ATS score")
    human_review_status: str = Field(default="approved", description="Human review status")
    human_review_notes: str = Field(..., description="Human review notes")
    resume_deltas: List[ResumeDelta] = Field(..., description="Individual bullet changes")


class TranslationEvent(BaseModel):
    """Translation event logging model."""
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


# Validation Functions

def validate_resume_deltas(deltas: List[ResumeDelta]) -> Dict[str, Any]:
    """Validate resume deltas against business rules."""
    allowed_operations = {'rephrase', 'reorder', 'emphasize', 'omit'}
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    for i, delta in enumerate(deltas):
        # Check operation is allowed
        if delta.operation not in allowed_operations:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Delta {i}: Invalid operation '{delta.operation}'. Must be one of: {allowed_operations}"
            )
        
        # Check for potential fabrication (demo logic)
        if delta.operation == "rephrase" and delta.to_text:
            if len(delta.to_text.split()) > len(delta.from_text.split()) * 1.5:
                validation_results["warnings"].append(
                    f"Delta {i}: Significant text expansion detected - review for fabrication"
                )
    
    return validation_results


# API Endpoints

@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "SmartApply Architecture Demo",
        "endpoints": {
            "role_analysis": "/human/role-analysis/validate",
            "resume_optimization": "/human/resume-optimization/validate",
            "translation_event": "/human/translation-event/validate"
        }
    }


@app.post("/human/role-analysis/validate")
def validate_role_analysis(ra: RoleAnalysis):
    """Validate role analysis data structure."""
    logger.info(f"Validating role analysis for job {ra.job_posting_id}")
    
    # Demo validation logic
    validation_results = {
        "valid": True,
        "warnings": []
    }
    
    if ra.overall_fit_score < 50 and ra.estimated_application_priority == "high":
        validation_results["warnings"].append(
            "Low fit score with high priority - review reasoning"
        )
    
    return {
        "ok": True,
        "received": ra,
        "validation": validation_results,
        "demo_note": "In production, this would store to Supabase with full audit trail"
    }


@app.post("/human/resume-optimization/validate")
def validate_resume_optimization(ro: ResumeOptimization):
    """Validate resume optimization with delta checking."""
    logger.info(f"Validating resume optimization for role analysis {ro.role_analysis_id}")
    
    # Validate resume deltas
    delta_validation = validate_resume_deltas(ro.resume_deltas)
    
    if not delta_validation["valid"]:
        raise HTTPException(status_code=400, detail=delta_validation["errors"])
    
    return {
        "ok": True,
        "received": ro,
        "delta_validation": delta_validation,
        "demo_note": "In production, this would enforce master_bullet FK constraints"
    }


@app.post("/human/translation-event/validate")
def validate_translation_event(te: TranslationEvent):
    """Validate translation event logging."""
    logger.info(f"Validating translation event for role analysis {te.role_analysis_id}")
    
    validation_results = {
        "valid": True,
        "term_mappings": len(te.original_terms),
        "processing_efficiency": f"{te.processing_time_ms}ms"
    }
    
    return {
        "ok": True,
        "received": te,
        "validation": validation_results,
        "demo_note": "In production, this would update concept mapping success rates"
    }


@app.get("/demo/schema-info")
def get_schema_info():
    """Demo endpoint showing schema highlights."""
    return {
        "tables": 19,
        "key_features": [
            "UUID primary keys",
            "Row Level Security (RLS)",
            "Strategic indexes",
            "Audit trails",
            "JSON support for flexible data"
        ],
        "core_tables": [
            "job_postings",
            "role_analyses", 
            "resume_optimizations",
            "resume_deltas",
            "concept_mappings",
            "translation_events"
        ],
        "demo_note": "Full schema available in sql/schema.sql"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)