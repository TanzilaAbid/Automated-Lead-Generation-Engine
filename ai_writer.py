"""
Uses an LLM (via Groq) to draft a short, personalized outreach email based
on what we know about the business: category, rating, and whether it has
a website.
"""
from groq import Groq, GroqError

from config import settings
from logger import get_logger

log = get_logger(__name__)

client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You write short, specific cold outreach emails for a \
freelance automation/marketing consultant reaching out to local businesses. \
Rules:
- Under 120 words.
- Identify ONE concrete, plausible pain point from the info given \
(e.g. no website, a mediocre rating, no visible online booking) and speak to it.
- No generic filler like "I hope this finds you well" or "I came across your business".
- End with a low-friction call to action (a short reply, not a meeting request).
- Plain text only, no subject line, no signature block."""


def generate_email(
    business_name: str,
    category: str,
    city: str,
    rating: float | None,
    has_website: bool,
) -> str | None:
    pain_point_hint = (
        "no website was found, so lead with visibility/discoverability"
        if not has_website
        else f"they have a website; rating is {rating}, factor that in if it's notable"
    )

    user_prompt = (
        f"Business: {business_name}\n"
        f"Category: {category}\n"
        f"City: {city}\n"
        f"Context: {pain_point_hint}\n\n"
        "Write the outreach email."
    )

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=400,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        email_body = response.choices[0].message.content.strip()
        return email_body or None

    except GroqError as exc:
        log.error("AI email generation failed for %s: %s", business_name, exc)
        return None