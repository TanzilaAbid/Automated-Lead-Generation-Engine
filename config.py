"""
Centralized configuration. Loads and validates environment variables once,
so every other module just does `from config import settings`.
"""
import os
import sys
from dataclasses import dataclass
 
from dotenv import load_dotenv
 
load_dotenv()
 
REQUIRED_VARS = [
    "RAPIDAPI_KEY",
    "RAPIDAPI_HOST",
    "GOOGLE_SHEETS_CREDENTIALS_PATH",
    "GOOGLE_SHEET_ID",
    "GROQ_API_KEY",
]
 
 
@dataclass(frozen=True)
class Settings:
    rapidapi_key: str
    rapidapi_host: str
    google_sheets_credentials_path: str
    google_sheet_id: str
    groq_api_key: str
    groq_model: str
    min_rating_threshold: float
    max_leads_per_run: int
    request_timeout_seconds: int
    search_country_code: str
    search_language_code: str
 
 
def _load_settings() -> Settings:
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        sys.exit(
            "Missing required environment variables: "
            f"{', '.join(missing)}. Copy .env.example to .env and fill "
            "them in before running the pipeline."
        )
 
    return Settings(
        rapidapi_key=os.environ["RAPIDAPI_KEY"],
        rapidapi_host=os.environ["RAPIDAPI_HOST"],
        google_sheets_credentials_path=os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"],
        google_sheet_id=os.environ["GOOGLE_SHEET_ID"],
        groq_api_key=os.environ["GROQ_API_KEY"],
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        min_rating_threshold=float(os.getenv("MIN_RATING_THRESHOLD", "3.5")),
        max_leads_per_run=int(os.getenv("MAX_LEADS_PER_RUN", "20")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "8")),
        search_country_code=os.getenv("SEARCH_COUNTRY_CODE", "pk"),
        search_language_code=os.getenv("SEARCH_LANGUAGE_CODE", "en"),
    )
 
 
settings = _load_settings()