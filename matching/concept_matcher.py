import re
from typing import Dict, Tuple
from collections import defaultdict

# === CONCEPT GROUPINGS FROM RESUME RESEARCH ===

CONCEPT_MAP = {
    "Resume A": {
        "platform_infrastructure": [
            "platform infrastructure", "system architecture", "infrastructure modernization", "CI/CD", "microservices",
            "infrastructure as code", "cloud infrastructure", "kubernetes", "terraform", "api design", "api integration"
        ],
        "data_platforms": [
            "data platform", "databricks", "data mart", "schema documentation", "real-time dashboards", "spark"
        ],
        "api_strategy": [
            "rest api", "graphql", "api-first", "integration strategy"
        ],
        "observability": [
            "metrics", "prometheus", "grafana", "logging", "instrumentation", "SLA", "monitoring", "alerts"
        ]
    },
    "Resume B": {
        "developer_tools": [
            "developer productivity", "developer experience", "internal developer platforms", "ide integrations", "build tooling", 
            "test frameworks", "release velocity", "dev workflow", "platform reliability"
        ],
        "observability": [
            "observability", "monitoring", "tracing", "logging", "dashboards", "metrics", "alerts", "incident resolution", "pendo"
        ],
        "ci_cd": [
            "CI/CD", "testing pipeline", "integration testing", "automated testing", "build system", "release stability"
        ]
    },
    "Resume C": {
        "billing_platform": [
            "billing platform", "monetization", "usage-based billing", "quote to cash", "payments platform",
            "invoicing", "chargeback", "reconciliation", "billing pipeline", "financial workflows"
        ],
        "revenue_metrics": [
            "ARR", "MRR", "revenue integrity", "billing metrics", "pricing logic", "financial SLA"
        ],
        "automation": [
            "workflow automation", "billing automation", "api-driven billing", "payment processing"
        ]
    },
    "Resume D": {
        "internal_tools": [
            "internal tools", "workflow tools", "productivity platforms", "collaboration tooling",
            "work management", "internal systems"
        ],
        "self_serve": [
            "self-serve", "adoption metrics", "kpi dashboards", "usability", "internal usage", "platform adoption"
        ],
        "developer_experience": [
            "developer efficiency", "internal developer experience", "tooling for engineers", "efficiency tooling"
        ]
    }
}

# === FLATTEN INTO REVERSE LOOKUP ===

KEYWORD_LOOKUP = {}
for resume, concept_map in CONCEPT_MAP.items():
    for concept, keywords in concept_map.items():
        for keyword in keywords:
            KEYWORD_LOOKUP[keyword.lower()] = (resume, concept)

# === CLEANING AND MATCHING FUNCTIONS ===

def clean_text(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())

def calculate_concept_alignment(job_description: str) -> Dict[str, Dict[str, int]]:
    cleaned = clean_text(job_description)
    concept_scores = defaultdict(lambda: defaultdict(int))
    for keyword, (resume, concept) in KEYWORD_LOOKUP.items():
        if keyword in cleaned:
            concept_scores[resume][concept] += 1
    return dict(concept_scores)

def score_all_resumes(concept_scores: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    return {resume: sum(concepts.values()) for resume, concepts in concept_scores.items()}

def recommend_optimal_resume(resume_scores: Dict[str, int]) -> Tuple[str, int]:
    if not resume_scores:
        return "None", 0
    best_resume = max(resume_scores.keys(), key=lambda k: resume_scores[k])
    return best_resume, resume_scores[best_resume]

# === MAIN FUNCTION FOR YOUR SYSTEM ===

def analyze_job_posting(job_description: str, company: str) -> Dict:
    concept_scores = calculate_concept_alignment(job_description)
    resume_scores = score_all_resumes(concept_scores)
    best_resume, match_score = recommend_optimal_resume(resume_scores)

    return {
        "company": company,
        "match_score": match_score,
        "recommended_resume": best_resume,
        "resume_match_breakdown": resume_scores,
        "concept_breakdown": concept_scores.get(best_resume, {})
    }

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    job_description = """
    We're looking for a Product Manager to lead our internal work management platform. 
    You'll improve productivity tooling, collaborate with engineering to scale internal workflows, 
    and drive adoption of self-serve solutions that improve developer efficiency.
    """
    company = "Spotify"
    result = analyze_job_posting(job_description, company)
    print(result)