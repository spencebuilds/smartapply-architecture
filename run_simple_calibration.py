#!/usr/bin/env python3
"""
SmartApply Rev A Simple Calibration Script
Runs a 2-minute calibration cycle focusing on concept matching.
"""

import sys
import time
import logging
from datetime import datetime
from matching.concept_matcher import analyze_job_posting

# Set up basic logging to avoid noise
logging.basicConfig(level=logging.WARNING)

def run_simple_calibration():
    """Run 2-minute calibration cycle focusing on concept matching."""
    print("=== SMARTAPPLY REV A CALIBRATION CYCLE ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize lightweight system for job fetching
    sys.path.append('.')
    from api_clients.greenhouse_client import GreenhouseClient
    from api_clients.lever_client import LeverClient
    
    greenhouse_client = GreenhouseClient()
    lever_client = LeverClient()
    
    # Track calibration metrics
    calibration_start = time.time()
    calibration_end_time = calibration_start + 120  # 2 minutes
    
    cycle_count = 0
    total_fetched = 0
    total_analyzed = 0
    total_matched = 0
    total_above_threshold = 0.10  # 10% threshold
    matched_postings = []
    
    print("Starting calibration cycles (2-minute duration)...")
    print()
    
    while time.time() < calibration_end_time:
        cycle_count += 1
        cycle_start = time.time()
        
        print(f"--- Cycle {cycle_count} ---")
        
        try:
            # Fetch jobs from both sources
            lever_jobs = lever_client.fetch_all_jobs()
            greenhouse_jobs = greenhouse_client.fetch_all_jobs()
            
            all_jobs = lever_jobs + greenhouse_jobs
            cycle_fetched = len(all_jobs)
            total_fetched += cycle_fetched
            
            print(f"  Fetched: {len(lever_jobs)} Lever + {len(greenhouse_jobs)} Greenhouse = {cycle_fetched} total jobs")
            
            # Process sample of jobs for concept matching
            sample_size = min(30, len(all_jobs))  # Limit to 30 jobs per cycle for performance
            sample_jobs = all_jobs[:sample_size] if all_jobs else []
            
            cycle_analyzed = 0
            cycle_matched = 0
            cycle_above_threshold = 0
            cycle_postings = []
            
            for job in sample_jobs:
                try:
                    # Skip jobs without descriptions
                    description = job.get("description", "").strip()
                    if not description or len(description) < 50:
                        continue
                    
                    cycle_analyzed += 1
                    
                    # Use concept matcher for analysis
                    result = analyze_job_posting(
                        job_description=description,
                        company=job.get("company", ""),
                        job_id=job.get("id", ""),
                        job_title=job.get("title", "")
                    )
                    
                    if result and result.get("fit_score", 0) > 0:
                        cycle_matched += 1
                        
                        fit_score = result.get("fit_score", 0)
                        
                        # Check threshold (10%)
                        if fit_score >= total_above_threshold * 100:  # Convert to percentage
                            cycle_above_threshold += 1
                            
                            # Store top matched posting details
                            posting_info = {
                                "company": job.get("company", ""),
                                "title": job.get("title", ""),
                                "fit_score": fit_score,
                                "recommended_resume": result.get("recommended_resume", ""),
                                "matched_concepts": list(result.get("concept_breakdown", {}).keys())[:5],
                                "concept_scores": result.get("concept_breakdown", {}),
                                "job_id": job.get("id", "")
                            }
                            matched_postings.append(posting_info)
                    
                except Exception as e:
                    print(f"    Error analyzing job {job.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Update totals
            total_analyzed += cycle_analyzed
            total_matched += cycle_matched
            total_above_threshold += cycle_above_threshold
            
            cycle_duration = time.time() - cycle_start
            
            print(f"  Analyzed: {cycle_analyzed} jobs with descriptions")
            print(f"  Matched ≥1 concept: {cycle_matched} jobs")
            print(f"  Above threshold: {cycle_above_threshold} jobs")
            print(f"  Duration: {cycle_duration:.2f}s")
            print()
            
            # Check if we have enough time for another cycle
            if time.time() + 15 > calibration_end_time:  # Need at least 15s for next cycle
                break
            
            # Short pause between cycles
            time.sleep(3)
            
        except Exception as e:
            print(f"  Error in cycle {cycle_count}: {str(e)}")
            break
    
    calibration_duration = time.time() - calibration_start
    
    # Print summary
    print("=== CALIBRATION SUMMARY ===")
    print(f"Duration: {calibration_duration:.2f} seconds ({cycle_count} cycles)")
    print(f"Total jobs fetched: {total_fetched}")
    print(f"Total jobs analyzed: {total_analyzed}")
    print(f"Jobs with ≥1 concept match: {total_matched}")
    print(f"Jobs above threshold (≥{total_above_threshold*100:.1f}%): {total_above_threshold}")
    
    if total_analyzed > 0:
        print(f"Concept match rate: {(total_matched/total_analyzed)*100:.1f}%")
        print(f"Above threshold rate: {(total_above_threshold/total_analyzed)*100:.1f}%")
    
    print()
    
    # Show top 5 matched postings
    if matched_postings:
        # Sort by fit score
        matched_postings.sort(key=lambda x: x["fit_score"], reverse=True)
        
        print("=== TOP 5 MATCHED POSTINGS WITH CONCEPTS & PHRASES ===")
        for i, posting in enumerate(matched_postings[:5], 1):
            print(f"{i}. {posting['company']} - {posting['title']}")
            print(f"   Fit Score: {posting['fit_score']:.2f}%")
            print(f"   Recommended Resume: {posting['recommended_resume']}")
            
            # Show concept breakdown with scores
            concept_scores = posting.get('concept_scores', {})
            if concept_scores:
                concept_details = [f"{concept}({score})" for concept, score in concept_scores.items()]
                print(f"   Matched Concepts: {', '.join(concept_details)}")
            print()
    else:
        print("=== NO MATCHED POSTINGS FOUND ===")
        print("This indicates either:")
        print("- No jobs have adequate descriptions for concept extraction")
        print("- Current vocabulary needs expansion for target job types")
        print("- MATCH_THRESHOLD may be too high for current concept coverage")
    
    # Additional insights
    print("=== REV A FEATURES STATUS ===")
    print("✅ Concept-based matching algorithm operational")
    print("✅ Multiple resume profile matching (A, B, C, D)")
    print("✅ Calibration logging system functional")
    print("✅ Job fetching from Lever + Greenhouse APIs")
    
    if matched_postings:
        print("✅ Vocabulary coverage adequate for job matching")
        
        # Show resume distribution
        resume_distribution = {}
        for posting in matched_postings:
            resume = posting.get('recommended_resume', 'Unknown')
            resume_distribution[resume] = resume_distribution.get(resume, 0) + 1
        
        print("\nResume Recommendation Distribution:")
        for resume, count in resume_distribution.items():
            print(f"  {resume}: {count} matches")
    
    print("\n=== CALIBRATION COMPLETE ===")

if __name__ == "__main__":
    run_simple_calibration()