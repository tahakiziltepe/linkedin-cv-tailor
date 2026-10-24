import logging
import pandas as pd
from jobspy import scrape_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_jobs(query: str, location: str, results_wanted: int = 3, hours_old: int = 1680):
    """
    Searches for jobs on LinkedIn using JobSpy.
    
    Args:
        query (str): Job title or keywords (e.g., "Python Developer").
        location (str): Location (e.g., "Istanbul, Turkey").
        results_wanted (int): Max number of results to return.
        hours_old (int): Filter for jobs posted within X hours.
        
    Returns:
        List[dict]: A list of dictionaries containing job details.
    """
    logger.info(f"Searching for '{query}' in '{location}' (Limit: {results_wanted}, Hours Old: {hours_old})...")
    
    try:
        jobs: pd.DataFrame = scrape_jobs(
            site_name=["linkedin"],
            search_term=query,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_nameof='Turkey',
            linkedin_fetch_description=True # Explicitly fetch description
        )
        
        if jobs.empty:
            logger.warning("No jobs found.")
            return []
            
        logger.info(f"Found {len(jobs)} jobs.")
        return jobs.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error occurring during job search: {e}")
        return []


