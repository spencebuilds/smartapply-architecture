#!/usr/bin/env python3
"""
Comprehensive calibration report for SmartApply concept matcher.
"""

import sys
sys.path.append('.')
from matching.concept_matcher import analyze_job_posting

# Create diverse job samples for calibration
job_samples = [
    {
        'id': 'cal_001', 
        'company': 'TechCorp', 
        'title': 'Senior Product Manager - Platform Infrastructure',
        'description': '''
        Lead platform infrastructure initiatives including kubernetes deployment, 
        terraform infrastructure as code, CI/CD pipelines, and API design. 
        Work with engineering teams on microservices architecture, observability metrics, 
        monitoring dashboards, and system reliability. Experience with prometheus, grafana, 
        and data platform technologies required.
        '''
    },
    {
        'id': 'cal_002',
        'company': 'DevTools Inc', 
        'title': 'Product Manager - Developer Experience',
        'description': '''
        Own developer productivity tools and internal developer platforms. 
        Build IDE integrations, improve build tooling, enhance test frameworks, 
        and increase release velocity. Focus on developer experience, platform reliability,
        and dev workflow optimization. Observability and incident resolution experience preferred.
        '''
    },
    {
        'id': 'cal_003',
        'company': 'PaymentCo',
        'title': 'Product Manager - Billing Platform', 
        'description': '''
        Drive billing platform strategy and monetization initiatives. 
        Own usage-based billing systems, payments platform, invoicing workflows,
        and quote to cash processes. Work on billing automation, payment processing,
        ARR/MRR revenue metrics, and financial SLA compliance.
        '''
    },
    {
        'id': 'cal_004',
        'company': 'WorkTools',
        'title': 'Product Manager - Internal Tools',
        'description': '''
        Build internal tools and productivity platforms for engineering teams.
        Focus on workflow automation, self-serve solutions, collaboration tooling,
        and work management systems. Drive platform adoption through KPI dashboards,
        usability improvements, and developer efficiency metrics.
        '''
    },
    {
        'id': 'cal_005',
        'company': 'GenericCorp',
        'title': 'Product Manager - Customer Analytics', 
        'description': '''
        Drive customer analytics and data visualization initiatives.
        Build user engagement tracking, customer journey analytics, 
        conversion funnel optimization, and retention metrics.
        Partner with data science on predictive models and segmentation.
        '''
    }
]

def main():
    print('=== SMARTAPPLY CONCEPT MATCHER CALIBRATION REPORT ===\n')

    results = []
    for job in job_samples:
        result = analyze_job_posting(
            job_description=job['description'],
            company=job['company'], 
            job_id=job['id'],
            job_title=job['title']
        )
        results.append((job, result))

    # Sort by fit_score descending
    results.sort(key=lambda x: x[1].get('fit_score', 0), reverse=True)

    # Count matches
    jobs_with_matches = sum(1 for _, result in results if result.get('fit_score', 0) > 0)
    jobs_above_threshold = sum(1 for _, result in results if result.get('fit_score', 0) >= 10)

    print('CALIBRATION SUMMARY:')
    print(f'  Total jobs tested: {len(results)}')
    print(f'  Jobs with ≥1 concept match: {jobs_with_matches}')
    print(f'  Jobs above 10% threshold: {jobs_above_threshold}')
    print()

    print('TOP 5 JOBS BY FIT SCORE:')
    for i, (job, analysis) in enumerate(results[:5], 1):
        fit_score = analysis.get('fit_score', 0)
        
        print(f'{i}. {job["company"]} - {job["title"]}')
        print(f'   Fit Score: {fit_score:.2f}%')
        print(f'   Recommended Resume: {analysis.get("recommended_resume", "None")}')
        
        # Get matched concepts
        concept_breakdown = analysis.get('concept_breakdown', {})
        if concept_breakdown:
            top_concepts = sorted(concept_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
            matched_phrases = [f'{concept}({count})' for concept, count in top_concepts]
            concepts_str = ', '.join(matched_phrases)
            print(f'   Top Matched Concepts: {concepts_str}')
        print()

    # Show jobs with 0 concepts (vocabulary gaps)
    zero_concept_jobs = [(job, result) for job, result in results if result.get('fit_score', 0) == 0]
    if zero_concept_jobs:
        print('JOBS WITH ZERO CONCEPTS (Vocabulary Gaps):')
        for i, (job, result) in enumerate(zero_concept_jobs[:3], 1):
            print(f'{i}. {job["company"]} - {job["title"]}')
            print(f'   Description sample: {job["description"][:100]}...')
            print()

    print('=== END CALIBRATION REPORT ===')

if __name__ == '__main__':
    main()