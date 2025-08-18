#!/usr/bin/env python3
"""
SmartApply Rev A Calibration Script
Runs a 2-minute calibration cycle and prints comprehensive summary.
"""

import sys
import time
import logging
from datetime import datetime
from main import JobApplicationSystem

def run_calibration():
    """Run 2-minute calibration cycle with Rev A features."""
    print("=== SMARTAPPLY REV A CALIBRATION CYCLE ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize system
    system = JobApplicationSystem()
    
    # Track calibration metrics
    calibration_start = time.time()
    calibration_end_time = calibration_start + 120  # 2 minutes
    
    cycle_count = 0
    total_fetched = 0
    total_analyzed = 0
    total_matched = 0
    total_above_threshold = 0
    matched_postings = []
    
    print("Starting calibration cycles (2-minute duration)...")
    print()
    
    while time.time() < calibration_end_time:
        cycle_count += 1
        cycle_start = time.time()
        
        print(f"--- Cycle {cycle_count} ---")
        
        try:
            # Run job cycle in calibration mode
            result = system.run_job_cycle(calibration_mode=True)
            
            # Update metrics
            total_fetched += result.get("total_fetched", 0)
            
            # For calibration, we'll analyze jobs manually
            jobs = system.fetch_all_jobs()
            
            # Process sample of jobs for concept matching
            sample_size = min(50, len(jobs))  # Limit to 50 jobs per cycle for performance
            sample_jobs = jobs[:sample_size] if jobs else []
            
            cycle_analyzed = 0
            cycle_matched = 0
            cycle_above_threshold = 0
            cycle_postings = []
            
            for job in sample_jobs:
                try:
                    # Skip jobs without descriptions
                    if not job.get("description", "").strip():
                        continue
                    
                    cycle_analyzed += 1
                    
                    # Use concept matcher for analysis
                    match_result = system.keyword_matcher.match_job(job)
                    
                    if match_result and match_result.get("best_match_score", 0) > 0:
                        cycle_matched += 1
                        
                        fit_score = match_result.get("best_match_score", 0)
                        
                        # Check threshold (0.10 = 10%)
                        if fit_score >= system.config.MATCH_THRESHOLD * 100:  # Convert decimal to percentage
                            cycle_above_threshold += 1
                            
                            # Store top matched posting details
                            posting_info = {
                                "company": job.get("company", ""),
                                "title": job.get("title", ""),
                                "fit_score": fit_score,
                                "recommended_resume": match_result.get("best_match_profile", ""),
                                "matched_concepts": list(match_result.get("concept_breakdown", {}).keys())[:5],
                                "job_id": job.get("id", "")
                            }
                            matched_postings.append(posting_info)
                    
                except Exception as e:
                    logging.error(f"Error analyzing job {job.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Update totals
            total_analyzed += cycle_analyzed
            total_matched += cycle_matched
            total_above_threshold += cycle_above_threshold
            
            cycle_duration = time.time() - cycle_start
            
            print(f"  Fetched: {result.get('total_fetched', 0)} jobs")
            print(f"  Analyzed: {cycle_analyzed} jobs")
            print(f"  Matched ≥1 concept: {cycle_matched} jobs")
            print(f"  Above threshold: {cycle_above_threshold} jobs")
            print(f"  Duration: {cycle_duration:.2f}s")
            print()
            
            # Check if we have enough time for another cycle
            if time.time() + 10 > calibration_end_time:  # Need at least 10s for next cycle
                break
            
            # Short pause between cycles
            time.sleep(2)
            
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
    print(f"Jobs above threshold (≥{system.config.MATCH_THRESHOLD*100:.1f}%): {total_above_threshold}")
    
    if total_analyzed > 0:
        print(f"Concept match rate: {(total_matched/total_analyzed)*100:.1f}%")
        print(f"Above threshold rate: {(total_above_threshold/total_analyzed)*100:.1f}%")
    
    print()
    
    # Show top 5 matched postings
    if matched_postings:
        # Sort by fit score
        matched_postings.sort(key=lambda x: x["fit_score"], reverse=True)
        
        print("=== TOP 5 MATCHED POSTINGS ===")
        for i, posting in enumerate(matched_postings[:5], 1):
            print(f"{i}. {posting['company']} - {posting['title']}")
            print(f"   Fit Score: {posting['fit_score']:.2f}%")
            print(f"   Recommended Resume: {posting['recommended_resume']}")
            
            concepts_str = ", ".join(posting['matched_concepts'])
            if concepts_str:
                print(f"   Top Concepts: {concepts_str}")
            print()
    else:
        print("=== NO MATCHED POSTINGS FOUND ===")
        print("Consider lowering the MATCH_THRESHOLD or improving concept vocabulary.")
    
    print("=== CALIBRATION COMPLETE ===")

if __name__ == "__main__":
    run_calibration()