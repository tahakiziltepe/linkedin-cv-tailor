import os
import logging
import time
import random
import functools
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.prompts import render_prompt

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = None
GEMINI_MODEL_PRO="gemini-3.1-flash-lite-preview"
GEMINI_MODEL_FLASH="gemini-3.1-flash-lite-preview"

if not api_key:
    logger.warning("GEMINI_API_KEY not found in environment variables.")
else:
    client = genai.Client(api_key=api_key)

generation_config = types.GenerateContentConfig(
    temperature=0.2,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

def retry_with_backoff(max_retries=5, initial_delay=2, backoff_factor=2, jitter=True):
    """
    Decorator to retry a function call with exponential backoff.
    Retries on exceptions that resemble rate limiting or transient errors.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Global rate limit delay between ANY calls
            time.sleep(2) 
            
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # Check for 429 or Resource Exhausted errors
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        if attempt == max_retries:
                            logger.error(f"Max retries reached for {func.__name__}. Last error: {e}")
                            raise e
                        
                        sleep_time = delay
                        if jitter:
                            sleep_time += random.uniform(0, 1)
                        
                        logger.warning(f"Rate limit hit in {func.__name__}. Retrying in {sleep_time:.2f}s (Attempt {attempt + 1}/{max_retries})...")
                        time.sleep(sleep_time)
                        delay *= backoff_factor
                    else:
                        raise e 
            return None # Should not be reached
        return wrapper
    return decorator

@retry_with_backoff(max_retries=5, initial_delay=10)
def _check_job_suitability_api(job_description: str) -> bool:
    """Internal function to call Gemini API for job suitability."""
    if not client:
        return True # Should probably not happen if called correctly, or handle outside

    logger.info("Checking job suitability...")
    
    prompt = render_prompt("suitability", JOB_DESCRIPTION=job_description)
 
    response = client.models.generate_content(
        model=GEMINI_MODEL_FLASH,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0)
    )
    result = response.text.strip().upper()
    logger.info(f"Job Suitability: {result}")
    return "YES" in result

def check_job_suitability(job_description: str) -> bool:
    """
    Checks if the job is suitable using Gemini based on specific criteria.
    Has retry logic and fail-safe fallback.
    """
    if not client:
        return True

    try:
        return _check_job_suitability_api(job_description)
    except Exception as e:
        logger.error(f"Error checking suitability after retries: {e}")
        return True # Default to True on error

@retry_with_backoff(max_retries=5, initial_delay=10)
def _tailor_cv_api(base_cv_content: str, job_description: str) -> str:
    """Internal function to call Gemini API for CV tailoring."""
    if not client:
        return base_cv_content

    logger.info("Tailoring CV with Gemini...")
    
    prompt = render_prompt(
        "tailor_cv",
        BASE_CV_TYPST=base_cv_content,
        JOB_DESCRIPTION=job_description,
    )
    
    response = client.models.generate_content(
        model=GEMINI_MODEL_PRO,
        contents=prompt,
        config=generation_config
    )
    tailored_content = response.text
    
    # Cleanup if Gemini returns markdown code blocks
    if tailored_content.startswith("```"):
        lines = tailored_content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        tailored_content = "\n".join(lines)
        
    logger.info("CV tailored successfully.")
    return tailored_content

def tailor_cv(base_cv_content: str, job_description: str) -> str:
    """
    Wrapper for CV tailoring with retry logic.
    """
    if not client:
        return base_cv_content

    try:
        return _tailor_cv_api(base_cv_content, job_description)
    except Exception as e:
        logger.error(f"Error tailoring CV after retries: {e}")
        return base_cv_content # Return original as fallback

@retry_with_backoff(max_retries=5, initial_delay=10)
def _fix_typst_code_api(typst_code: str, error_message: str) -> str:
    """Internal function to call Gemini API for fixing Typst code."""
    if not client:
        return typst_code

    # Add extra delay before fixing code, as requested by user
    logger.info("Waiting 10 seconds before attempting to fix Typst code...")
    time.sleep(10)

    logger.info("Attempting to fix Typst code with Gemini...")
    
    prompt = render_prompt(
        "fix_typst",
        ERROR_MESSAGE=error_message,
        BROKEN_TYPST_CODE=typst_code,
    )
    
    response = client.models.generate_content(
        model=GEMINI_MODEL_FLASH,
        contents=prompt,
        config=generation_config
    )
    fixed_content = response.text
    
    # Cleanup
    if fixed_content.startswith("```"):
        lines = fixed_content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        fixed_content = "\n".join(lines)
        
    return fixed_content

def fix_typst_code(typst_code: str, error_message: str) -> str:
    """
    Wrapper for fixing Typst code with retry logic.
    """
    if not client:
        return typst_code

    try:
        return _fix_typst_code_api(typst_code, error_message)
    except Exception as e:
        logger.error(f"Error fixing Typst code after retries: {e}")
        return None
