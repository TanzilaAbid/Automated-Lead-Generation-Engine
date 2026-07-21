"""
Decides whether a lead should be contacted, and simulates sending.
No real email is sent -- this just returns a status + notes describing
what would have happened, which is what gets logged and written to the sheet.
"""
from typing import Optional, Tuple

from config import settings
from logger import get_logger

log = get_logger(__name__)


def evaluate_lead(
    email: Optional[str], rating: Optional[float]
) -> Tuple[str, str]:
    """Return (status, notes) without sending anything."""
    if rating is not None and rating < settings.min_rating_threshold:
        return "skipped_low_rating", f"Rating {rating} below threshold {settings.min_rating_threshold}"

    if not email:
        return "no_email_found", "No contact email could be extracted"

    return "eligible", "Passed rating and email checks"


def simulate_send(business_name: str, email: str, email_body: Optional[str]) -> Tuple[str, str]:
    """Simulate sending the outreach email. Returns (status, notes)."""
    if not email_body:
        return "ai_generation_failed", "AI failed to generate email content"

    log.info("SIMULATED SEND -> %s <%s>", business_name, email)
    return "queued", "Email generated and queued (simulated, not actually sent)"
