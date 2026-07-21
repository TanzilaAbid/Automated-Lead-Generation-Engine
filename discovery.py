"""
Lead discovery via the FlyByAPIs "Google Maps Extractor" API on RapidAPI.
https://rapidapi.com/flybyapi1/api/google-maps-extractor2
 
NOTE: RapidAPI listing UIs are JS-rendered, so the exact response field
names below are our best-effort guess based on the documented endpoint
(/locate_and_search). Before your first real run:
  1. Open the API on RapidAPI -> Endpoints tab -> /locate_and_search
  2. Click "Test Endpoint" with a sample query
  3. Compare the returned JSON keys against FIELD_CANDIDATES below and
     adjust if your response uses different key names.
"""
from typing import List, Optional, TypedDict
 
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
 
from config import settings
from logger import get_logger
 
log = get_logger(__name__)
 
BASE_URL = f"https://{settings.rapidapi_host}/locate_and_search"
 
HEADERS = {
    "X-RapidAPI-Key": settings.rapidapi_key,
    "X-RapidAPI-Host": settings.rapidapi_host,
}
 
# Confirmed from real /locate_and_search responses:
# top-level: {status, request_id, data: [...]}
# each item includes: place_id, name, address, full_address, website_url,
# website_domain, detailed_address {city, state, zip_code, country, ...},
# main_category, categories, latitude, longitude, owner_name, working_hours,
# rating, reviews_count, phone, full_phone (E.164 format, preferred).
FIELD_CANDIDATES = {
    "name": ("name", "title", "business_name"),
    "address": ("full_address", "address", "formatted_address"),
    "phone": ("full_phone", "phone", "international_phone_number"),
    "website": ("website_url", "website", "site", "url"),
    "rating": ("rating", "average_rating", "stars", "review_rating"),
    "place_id": ("place_id", "google_id", "id"),
}
 
 
class Lead(TypedDict, total=False):
    place_id: str
    name: str
    address: str
    rating: Optional[float]
    website: Optional[str]
    phone: Optional[str]
 
 
def _first_present(item: dict, keys: tuple) -> Optional[str]:
    for key in keys:
        if item.get(key) not in (None, ""):
            return item[key]
    return None
 
 
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,  # re-raise the original requests.RequestException on final failure,
    # instead of tenacity's default RetryError, so the except clause in
    # search_places() below can actually catch it.
)
def _call_api(params: dict) -> dict:
    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()
 
 
def _normalize(raw_item: dict) -> Lead:
    rating_raw = _first_present(raw_item, FIELD_CANDIDATES["rating"])
    try:
        rating = float(rating_raw) if rating_raw is not None else None
    except (TypeError, ValueError):
        rating = None
 
    return {
        "place_id": str(_first_present(raw_item, FIELD_CANDIDATES["place_id"]) or ""),
        "name": _first_present(raw_item, FIELD_CANDIDATES["name"]) or "Unknown",
        "address": _first_present(raw_item, FIELD_CANDIDATES["address"]) or "",
        "phone": _first_present(raw_item, FIELD_CANDIDATES["phone"]),
        "website": _first_present(raw_item, FIELD_CANDIDATES["website"]),
        "rating": rating,
    }
 
 
def search_places(category: str, city: str, max_results: int) -> List[Lead]:
    """Search for businesses matching `category` in `city` via RapidAPI."""
    query = f"{category} in {city}"
    log.info("Searching RapidAPI (Google Maps Extractor) for: %s", query)
 
    params = {
        "query": query,
        "offset": 0,
        "limit": max_results,
        "country": settings.search_country_code,
        "language": settings.search_language_code,
    }
 
    try:
        data = _call_api(params)
    except requests.RequestException as exc:
        log.error("RapidAPI search failed: %s", exc)
        return []
 
    # The results list may be at the top level, or nested under a key like
    # "results" / "data" / "businesses" depending on the actual response.
    raw_results = (
        data.get("results")
        or data.get("data")
        or data.get("businesses")
        or (data if isinstance(data, list) else [])
    )
 
    if not raw_results:
        log.warning("No results found in RapidAPI response. Raw keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))
        return []
 
    leads = [_normalize(item) for item in raw_results[:max_results]]
    log.info("Found %d leads", len(leads))
    return leads