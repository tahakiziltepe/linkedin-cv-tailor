import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging
from src.job_search import find_jobs
from src.cv_tailor import tailor_cv, check_job_suitability, fix_typst_code
from src.pdf_generator import render_pdf
from src.tracker import JobTracker
from src.notifier import notifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("CV_DATA_DIR", str(BASE_DIR / 'data')))
DATABASE_DIR = DATA_DIR / 'database'
OUTPUT_DIR = DATA_DIR / 'output'

def load_blocked_companies() -> list:
    """Loads the blocked companies list from data/blocked_companies.json."""
    blocked_file = DATA_DIR / 'blocked_companies.json'
    if not blocked_file.exists():
        return []
    try:
        with open(blocked_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        return [c.lower().strip() for c in companies if isinstance(c, str)]
    except Exception as e:
        logger.error(f"Failed to load blocked companies: {e}")
        return []

def is_blocked_company(company: str, blocked_companies: list) -> bool:
    """Checks if a company name matches any entry in the blocked companies list."""
    return company.lower().strip() in blocked_companies

def main():
    parser = argparse.ArgumentParser(description="LinkedIn CV Builder & Tailor")
    parser.add_argument("--query", "-q", type=str, required=True, help="Job search query (e.g. 'Python Developer')")
    parser.add_argument("--location", "-l", type=str, default="Istanbul, Turkey", help="Job location")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Number of jobs to process")
    parser.add_argument("--hours", type=int, default=24, help="Filter for jobs posted within X hours (default: 24)")
    
    args = parser.parse_args()
    
    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Read Base CV
    base_cv_path = DATA_DIR / 'base_cv.typ'
    if not base_cv_path.exists():
        logger.error(f"Base CV not found at {base_cv_path}")
        return
        
    with open(base_cv_path, 'r', encoding='utf-8') as f:
        base_cv_content = f.read()

    # Initialize Job Tracker
    tracker = JobTracker(DATABASE_DIR)

    # Load blocked companies
    blocked_companies = load_blocked_companies()
    if blocked_companies:
        logger.info(f"Loaded {len(blocked_companies)} blocked companies.")
        
    # 2. Search Jobs
    jobs = find_jobs(args.query, args.location, results_wanted=args.limit, hours_old=args.hours)
    if not jobs:
        logger.info("No jobs to process.")
        return
        
    # 3. Process each job
    for i, job in enumerate(jobs):
        title = job.get('title', 'Unknown_Title')
        company = job.get('company', 'Unknown_Company')
        job_description = job.get('description', '')
        job_url = job.get('job_url', '')
        
        logger.info(f"Processing Job {i+1}/{len(jobs)}: {title} at {company} | URL: {job_url}")
        
        if tracker.job_exists(job_url):
            logger.info(f"Skipping job {title}: Already tracked in history.")
            continue

        if not job_description:
            logger.warning(f"Skipping job {title} due to missing description.")
            continue

        # 4. Check Blocked Company
        if is_blocked_company(company, blocked_companies):
            logger.warning(f"Skipping job {title}: Company '{company}' is blocked.")
            tracker.add_job({
                "company": company,
                "title": title,
                "url": job_url,
                "pdf_path": None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": args.query,
                "status": "Blocked Company"
            })
            continue
            
        # 5. Check Suitability
        if not check_job_suitability(job_description):
             logger.warning(f"Skipping job {title}: Deemed unsuitable by AI.")
             tracker.add_job({
                 "company": company,
                 "title": title,
                 "url": job_url,
                 "pdf_path": None,
                 "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "query": args.query,
                 "status": "Not Interested"
             })
             continue

        logger.info(f"Yess! Job '{title}' at '{company}' is suitable. Sending notification...")
        notifier.notify_suitable_job(job_title=title, company=company, url=job_url)

        # 5. Tailor CV
        tailored_typst = tailor_cv(base_cv_content, job_description)
        
        # 5. Generate Filename safe string
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        safe_company = "".join([c if c.isalnum() else "_" for c in company])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename_base = f"{safe_company}_{safe_title}_{timestamp}"
        
        output_pdf_path = OUTPUT_DIR / f"{filename_base}.pdf"
        
        # 6. Save and Compile
        try:
            render_pdf(tailored_typst, str(output_pdf_path))
            logger.info(f"Generated CV: {output_pdf_path}")
            tracker.add_job({
                "company": company,
                "title": title,
                "url": job_url,
                "pdf_path": output_pdf_path.name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": args.query
            })
        except Exception as e:
            logger.error(f"Initial compilation failed: {e}")
            
            # Auto-Recovery Loop
            current_typst = tailored_typst
            max_retries = 3
            
            for attempt in range(max_retries):
                logger.info(f"Attempting to fix Typst code (Attempt {attempt+1}/{max_retries})...")
                current_typst = fix_typst_code(current_typst, str(e))
                if current_typst is None:
                    logger.error("Automatic fix failed (API error). Skipping this job.")
                    break
                
                try:
                    render_pdf(current_typst, str(output_pdf_path))
                    logger.info(f"Generated CV (after fix): {output_pdf_path}")
                    tracker.add_job({
                        "company": company,
                        "title": title,
                        "url": job_url,
                        "pdf_path": output_pdf_path.name,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": args.query
                    })
                    break # Success
                except Exception as retry_error:
                   logger.error(f"Retry {attempt+1} failed: {retry_error}")
                   e = retry_error # Update error for next fix attempt
            else:
                logger.error(f"Failed to generate CV for {company} after {max_retries} retries.")

        # Rate Limit Protection
        logger.info("Waiting 20 seconds before processing next job to avoid rate limits...")
        import time
        time.sleep(20)

if __name__ == "__main__":
    main()
