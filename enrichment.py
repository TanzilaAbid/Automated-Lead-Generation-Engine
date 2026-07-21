"""
Enrichment step: given a business website, try to find a contact email.
The Places API does not return email addresses, so this is derived by
fetching the homepage (and a likely contact page) and scanning for
mailto: links / email-shaped text.
"""
import re
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import settings
from logger import get_logger

log = get_logger(__name__)

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Common false positives picked up from tracking scripts, image CDNs, etc.
IGNORED_DOMAINS = ("sentry.io", "wixpress.com", "example.com", "godaddy.com")

CANDIDATE_PATHS = ("", "/contact", "/contact-us", "/about")


def _extract_emails(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")

    found = set()

    for link in soup.select('a[href^="mailto:"]'):
        address = link["href"].replace("mailto:", "").split("?")[0].strip()
        found.add(address)

    for match in EMAIL_PATTERN.findall(soup.get_text(" ")):
        found.add(match)

    return {e for e in found if not any(d in e.lower() for d in IGNORED_DOMAINS)}


def find_email(website: Optional[str]) -> Optional[str]:
    """Return the first plausible contact email found on the site, or None."""
    if not website:
        return None

    base_url = website if website.startswith("http") else f"https://{website}"

    for path in CANDIDATE_PATHS:
        url = urljoin(base_url, path)
        try:
            response = requests.get(
                url,
                timeout=settings.request_timeout_seconds,
                headers={"User-Agent": "Mozilla/5.0 (compatible; LeadGenBot/1.0)"},
            )
            if response.status_code != 200:
                continue

            emails = _extract_emails(response.text)
            if emails:
                chosen = sorted(emails)[0]
                log.info("Found email %s at %s", chosen, url)
                return chosen

        except requests.RequestException as exc:
            log.warning("Could not fetch %s: %s", url, exc)
            continue

    log.info("No email found for %s", base_url)
    return None
