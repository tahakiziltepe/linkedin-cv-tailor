import os
import logging
import time
import random
import functools
from google import genai
from google.genai import types
from dotenv import load_dotenv

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
    
    prompt = f"""
    # ROLE
    You are a highly specialized Job Classification Engine.

    # PRIMARY TASK
    Your sole function is to analyze the provided job description and classify it into one of two categories based on the criteria below. Your response will be the category label itself.

    # CLASSIFICATION CRITERIA

    ## Category 1: "YES"
    This category includes roles that are fundamentally data-centric and part of a core data team.
    - **Keywords and Responsibilities**: Look for terms like ETL, Data Warehouse (DWH), Business Intelligence (BI), SQL, data modeling, data pipelines, data analytics, data governance, reporting, dashboards.
    - **Example Titles**: Data Engineer, DWH Developer, DWH Developer, Business Intelligence Specialist, Business Intelligence Developer.

    ## Category 2: "NO"
    This category includes all other roles, even if they interact with data peripherally.
    - **Keywords and Responsibilities**: Look for terms like data science, front-end/back-end development, API design, mobile application (iOS/Android), system administration, cloud infrastructure (unless purely for data platforms), UI/UX design, customer support, marketing analytics, sales operations, internship roles.
    - **Example Titles**: Assistant Specialist (Uzman Yardımcısı), Intern (Stajyer), Data Scientist, Business Analyst, Software Engineer, Web Developer, Mobile Developer, Systems Administrator, DevOps Engineer (general), Customer Experience Analyst, Product Owner, Configuration Engineer, Observability Engineer.
    
    # STRICT OUTPUT RULES
    1.  **Single Word Response**: Your output MUST be a single word.
    2.  **Valid Words Only**: The ONLY valid responses are 'YES' or 'NO'.
    3.  **No Extra Content**: Do NOT provide explanations, context, or any conversational text.
    4.  **Character Prohibition**: You MUST NOT use any special characters, including but not limited to '#' and ','. Your response must be the word itself and nothing more.

    # JOB DESCRIPTION TO CLASSIFY
    {job_description}
    """
 
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
    
    prompt = f"""
    # PERSPECTIVE
    You are an elite career strategist and an expert CV editor specializing in Data Engineering and Analytics roles. Your precision ensures the candidate's CV is not just "tailored" but "weaponized" for the specific role.

    # PRIMARY OBJECTIVE
    Transform the `BASE_CV_TYPST` into a high-impact document by selecting the most strategic responsibilities and achievements from the provided databases.

    # CORE TASK
    1.  **Analyze**: Scrutinize the provided `BASE_CV_TYPST` and the `JOB_DESCRIPTION`.
    2.  **Identify**: Extract key skills, qualifications, and keywords from the `JOB_DESCRIPTION`.
    3.  **Strategically Select, Rewrite & Reorder**:
        *   **Select for Relevance**: From the comprehensive list of responsibilities and achievements in the `BASE_CV_TYPST` for the most recent role, you must *select* the most impactful and relevant points that directly map to the `JOB_DESCRIPTION`'s requirements.
        *   **Reorder for Impact**: Once selected, prioritize and reorder the bullet points to place the most critical information first.
        *   **Rephrase for Alignment**: Modify the phrasing of the selected bullet points to incorporate keywords from the job description without losing the original meaning or truthfulness.
        *   **Structure the Latest Role**: For the most recent job experience, you MUST structure its description by selecting:
            *   Exactly three (3) bullet points for the `Job Description`.
            *   Exactly two (2) bullet points for the `Notable Achievements`. (If multiple versions of an achievement exist, e.g., V_SHORT/V_LONG, select the one that best fits the tone and detail level required by the job ad).
        *   **Generate Profile Section (MANDATORY)**:
            *   Locate the existing `== Profile` header in the `BASE_CV_TYPST`.
            *   Read the `Professional Summary Components` comment block immediately following it.
            *   Select 2-3 most relevant sentences matching the `JOB_DESCRIPTION`.
            *   **REPLACE** the entire comment block with your generated professional summary paragraph.
            *   **DO NOT** add a second `== Profile` header. The final output should have exactly one `== Profile` header followed by the summary text.
        *   **Generate Skills Section**:
            *   Locate the `== Skills` header and the commented-out skill database in `BASE_CV_TYPST`.
            *   Analyze the skill categories (e.g., Data Warehousing, Cloud Technologies) and the specific skills listed in the comments.
            *   For each category, **SELECT** and **PRIORITIZE** skills that are mentioned in or relevant to the `JOB_DESCRIPTION`. Do not place more skills than necessary; focus on quality over quantity.
            *   **NO HALLUCINATIONS**: You MUST NOT include any skill that is NOT present in the `BASE_CV_TYPST` skill database. If the job asks for "Scala" and you don't have it in your base CV, DO NOT ADD IT.
            *   **NO REDUNDANCY**: Do not list synonymous skills separately (e.g., if you list "PySpark", do not also list "Apache Spark" or "Spark"). Choose the most specific/relevant term.
            *   **REPLACE** the existing static list with your tailored, reordered list.
            *   **SELECTIVE CATEGORIES**: You do not need to list every single category if it is not relevant. For example, if the job is purely Data Engineering, you may omit "Web Development" or weak/irrelevant skills.
            *   **STRICT FORMAT**: You MUST maintain the exact format: `- *Category Name*: Skill 1, Skill 2, ...`
    4.  **Formulate Explanation**: Before generating the CV code, formulate a concise explanation of the key changes you made. This summary must detail *what* you changed (e.g., "Generated a tailored Profile focusing on Data Engineering...") and *why* you made those changes. Specifically indicate which section of the job posting the changes were made in reference to.
    5.  **Generate Final Output**: Construct the final output string. It must begin with the explanation from the previous step, perfectly enclosed within a Typst block comment (`/* ... */`). Immediately following the closing `*/`, append the complete, updated Typst CV code without any intermediate characters or lines.

    # CRITICAL RULES & OUTPUT CONSTRAINTS
    1.  **NO MARKDOWN**: Do NOT output markdown code blocks (e.g., ```typst ... ```). Output raw code only.
    2.  **PRESERVE IMPORTS**: Do NOT change imports or variable definitions at the top.
    3.  **UNCOMMENTED PROFILE**: The `== Profile` section content must be **PLAIN TEXT**, NOT commented out.
        *   **CORRECT:** `== Profile\nMy tailored summary...`
        *   **WRONG:** `== Profile\n/* My tailored summary */`
    4.  **STRICT STRUCTURE PRESERVATION (NO NESTING HALLUCINATION)**: 
        *   **Do NOT** change the call structure of `#work(...)`. 
        *   **Do NOT** pass bullet points as arguments to `#work()`.
        *   The `#work()` function MUST close with a `)`, and the bullet points must follow on new lines as standard Typst list items (starting with `-`).

    # INCORRECT STRUCTURE (DO NOT DO THIS):
    ```typst
    #work(
      title: "...",
      details: [ - My bullet point ] // WRONG! 'details' param does not exist in base_cv.typ
    )
    ```

    # CORRECT STRUCTURE (DO THIS):
    ```typst
    #work(
      title: "...",
      company: "...",
      dates: ...
    ) // Function closes here
    
    === Job Description
    - My bullet point 1
    - My bullet point 2
    ```
    
    5.  **NO HALLUCINATIONS**: Do not invent new parameters for defined functions. Do not use any technical term that is not present in the `BASE_CV_TYPST`.
    6.  **ONLY TYPST**: The output must be valid, compilable Typst code.
    7.  **Mandatory Comment Header**: The entire output MUST start with your explanation of changes, enclosed in a Typst block comment (`/* ... */`). There must be no characters, spaces, or newlines before the opening `/*`.
    8.  **Structure Preservation**: The fundamental Typst structure, commands, and layout of the `BASE_CV_TYPST` must be preserved IDENTICALLY in the CV portion of the output.
    -   **Content Authenticity**: You MUST NOT invent, fabricate, or exaggerate any information. All skills, experiences, and achievements must be derived directly from the `BASE_CV_TYPST`.
    -   **Data Preservation (CRITICAL)**: 
        *   **Do NOT touch the Header**: The name, location, email, github, linkedin, and phone definitions at the top MUST remain character-for-character INDENTICAL. 
        *   **Preserve Escapes**: You MUST preserve all backslash escapes in contact info. For example, a contact like `you\\@example.com` must remain `you\\@example.com`. Do NOT strip the backslash to `you@example.com`.
        *   **No "Fixing"**: Do not attempt to "correct" what looks like a typo in the contact info or imports. Leave it exactly as in `BASE_CV_TYPST`.
    -   **Language & Tone**: Use professional, fluent, and action-oriented English (e.g., "Managed," "Developed," "Accelerated"). The tone should be confident and competent. Preserve technical jargon from the original CV.
    -   **Length**: The total length of the generated CV should be within +/- 5% of the original `BASE_CV_TYPST`'s content length. Avoid significant shortening or lengthening.

    # INPUT DATA
    ## BASE_CV_TYPST:
    {base_cv_content}

    ## JOB_DESCRIPTION:
    {job_description}
    """
    
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
    
    prompt = f"""
    You are a Typst expert. The following Typst code failed to compile.
    
    ERROR MESSAGE:
    {error_message}
    
    BROKEN TYPST CODE:
    {typst_code}
    
    TASK:
    Fix the code to resolve the error. 
    1. Analyze the error message (e.g., "expected integer, found string").
    2. Locate the problematic line in the code.
    3. correct the syntax.
    4. Return ONLY the complete, fixed Typst code. Do not use markdown blocks.
    """
    
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
