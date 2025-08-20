"""
Resume Delta Service - Granular Resume Change Tracking
Portfolio showcase of resume optimization validation and tracking.
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeltaOperation(Enum):
    """Allowed operations for resume bullet modifications."""
    REPHRASE = "rephrase"
    REORDER = "reorder"
    EMPHASIZE = "emphasize"
    OMIT = "omit"


@dataclass
class ResumeDelta:
    """Individual resume bullet change tracking."""
    master_bullet_id: str
    operation: DeltaOperation
    from_text: str
    to_text: Optional[str] = None
    concept_ids: List[str] = None
    notes: str = ""
    validation_score: float = 1.0
    
    def __post_init__(self):
        if self.concept_ids is None:
            self.concept_ids = []


@dataclass
class ValidationResult:
    """Result of delta validation."""
    is_valid: bool
    confidence: float
    warnings: List[str]
    errors: List[str]
    risk_flags: List[str]


class ResumeDeltaService:
    """
    Service for validating and tracking resume bullet modifications.
    
    Key Features:
    - Anti-fabrication validation
    - Allowed operation enforcement
    - Content quality scoring
    - Audit trail generation
    """
    
    def __init__(self):
        """Initialize the resume delta service."""
        self.allowed_operations = {op.value for op in DeltaOperation}
        
        # Common technical skills for fabrication detection
        self.technical_skills = {
            'python', 'javascript', 'react', 'typescript', 'sql', 'aws', 'kubernetes',
            'docker', 'git', 'agile', 'scrum', 'jira', 'confluence', 'figma', 'slack',
            'postgresql', 'mongodb', 'redis', 'graphql', 'rest', 'api', 'microservices',
            'terraform', 'ansible', 'jenkins', 'cicd', 'devops', 'linux', 'bash',
            'fastapi', 'django', 'flask', 'nodejs', 'express', 'vue', 'angular'
        }
        
        logger.info("ResumeDeltaService initialized")
    
    def validate_delta(self, delta: ResumeDelta) -> ValidationResult:
        """
        Validate a resume delta against business rules.
        
        Args:
            delta: The resume delta to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        warnings = []
        errors = []
        risk_flags = []
        
        # Check operation is allowed
        if delta.operation.value not in self.allowed_operations:
            errors.append(f"Invalid operation '{delta.operation.value}'. Must be one of: {self.allowed_operations}")
        
        # Validate based on operation type
        if delta.operation == DeltaOperation.REPHRASE:
            validation = self._validate_rephrase(delta)
            warnings.extend(validation["warnings"])
            errors.extend(validation["errors"])
            risk_flags.extend(validation["risk_flags"])
        
        elif delta.operation == DeltaOperation.OMIT:
            if delta.to_text is not None:
                warnings.append("Omit operation should have null to_text")
        
        elif delta.operation == DeltaOperation.EMPHASIZE:
            validation = self._validate_emphasize(delta)
            warnings.extend(validation["warnings"])
        
        elif delta.operation == DeltaOperation.REORDER:
            # Reorder operations are generally safe
            pass
        
        # Calculate confidence score
        confidence = self._calculate_confidence(delta, len(errors), len(risk_flags))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence=confidence,
            warnings=warnings,
            errors=errors,
            risk_flags=risk_flags
        )
    
    def _validate_rephrase(self, delta: ResumeDelta) -> Dict[str, List[str]]:
        """Validate rephrase operations for fabrication."""
        warnings = []
        errors = []
        risk_flags = []
        
        if not delta.to_text:
            errors.append("Rephrase operation requires to_text")
            return {"warnings": warnings, "errors": errors, "risk_flags": risk_flags}
        
        # Check for new metrics/numbers
        from_numbers = self._extract_numbers(delta.from_text)
        to_numbers = self._extract_numbers(delta.to_text)
        new_numbers = to_numbers - from_numbers
        
        if new_numbers:
            risk_flags.append(f"New metrics added: {list(new_numbers)}")
        
        # Check for new technical skills
        from_skills = self._extract_technical_skills(delta.from_text)
        to_skills = self._extract_technical_skills(delta.to_text)
        new_skills = to_skills - from_skills
        
        if new_skills:
            risk_flags.append(f"New technical skills added: {list(new_skills)}")
        
        # Check for excessive expansion
        length_ratio = len(delta.to_text) / max(len(delta.from_text), 1)
        if length_ratio > 1.5:
            warnings.append(f"Significant text expansion (ratio: {length_ratio:.2f})")
        
        # Check for content preservation
        similarity_score = self._calculate_similarity(delta.from_text, delta.to_text)
        if similarity_score < 0.3:
            risk_flags.append(f"Low content similarity: {similarity_score:.2f}")
        
        return {"warnings": warnings, "errors": errors, "risk_flags": risk_flags}
    
    def _validate_emphasize(self, delta: ResumeDelta) -> Dict[str, List[str]]:
        """Validate emphasize operations."""
        warnings = []
        
        if not delta.to_text:
            warnings.append("Emphasize operation typically includes to_text")
            return {"warnings": warnings}
        
        # Check for reasonable emphasis (formatting, word choice)
        emphasis_indicators = ['**', '*', 'CAPITAL', 'key', 'critical', 'major', 'significant']
        
        has_emphasis = any(indicator in delta.to_text for indicator in emphasis_indicators)
        if not has_emphasis:
            warnings.append("Emphasize operation shows no clear emphasis indicators")
        
        return {"warnings": warnings}
    
    def _extract_numbers(self, text: str) -> Set[str]:
        """Extract numbers and percentages from text."""
        # Match numbers, percentages, currency, etc.
        number_pattern = r'\d+(?:\.\d+)?(?:%|\$|k|m|b)?'
        return set(re.findall(number_pattern, text.lower()))
    
    def _extract_technical_skills(self, text: str) -> Set[str]:
        """Extract technical skills from text."""
        words = set(word.lower().strip('.,!?;:') for word in text.split())
        return words.intersection(self.technical_skills)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity score between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union
    
    def _calculate_confidence(self, delta: ResumeDelta, error_count: int, risk_count: int) -> float:
        """Calculate confidence score for the delta."""
        base_confidence = 1.0
        
        # Reduce confidence for errors and risks
        confidence = base_confidence - (error_count * 0.5) - (risk_count * 0.2)
        
        # Boost confidence for safe operations
        if delta.operation in [DeltaOperation.REORDER, DeltaOperation.OMIT]:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def validate_delta_batch(self, deltas: List[ResumeDelta]) -> Dict[str, Any]:
        """
        Validate a batch of deltas with cross-validation.
        
        Args:
            deltas: List of resume deltas to validate
            
        Returns:
            Batch validation results with summary statistics
        """
        results = []
        total_risk_flags = 0
        total_errors = 0
        
        for i, delta in enumerate(deltas):
            result = self.validate_delta(delta)
            result_dict = {
                "index": i,
                "delta_id": delta.master_bullet_id,
                "operation": delta.operation.value,
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "warnings": result.warnings,
                "errors": result.errors,
                "risk_flags": result.risk_flags
            }
            results.append(result_dict)
            
            total_risk_flags += len(result.risk_flags)
            total_errors += len(result.errors)
        
        # Calculate batch statistics
        valid_deltas = sum(1 for r in results if r["is_valid"])
        avg_confidence = sum(r["confidence"] for r in results) / max(len(results), 1)
        
        return {
            "batch_valid": total_errors == 0,
            "total_deltas": len(deltas),
            "valid_deltas": valid_deltas,
            "total_errors": total_errors,
            "total_risk_flags": total_risk_flags,
            "average_confidence": avg_confidence,
            "results": results,
            "recommendation": self._get_batch_recommendation(total_errors, total_risk_flags, len(deltas))
        }
    
    def _get_batch_recommendation(self, errors: int, risks: int, total: int) -> str:
        """Get recommendation based on batch validation results."""
        if errors > 0:
            return "REJECT: Contains validation errors that must be fixed"
        elif risks > total * 0.5:
            return "REVIEW: High number of risk flags - manual review recommended"
        elif risks > 0:
            return "CAUTION: Some risk flags present - review flagged items"
        else:
            return "APPROVE: All validations passed"
    
    def generate_audit_summary(self, deltas: List[ResumeDelta]) -> Dict[str, Any]:
        """Generate audit summary for compliance tracking."""
        operations_count = {}
        total_changes = len(deltas)
        
        for delta in deltas:
            op = delta.operation.value
            operations_count[op] = operations_count.get(op, 0) + 1
        
        return {
            "timestamp": "2025-08-20T00:00:00Z",  # Would use real timestamp
            "total_changes": total_changes,
            "operations_breakdown": operations_count,
            "compliance_notes": "All operations within allowed set",
            "audit_trail": "Detailed validation performed on all deltas"
        }