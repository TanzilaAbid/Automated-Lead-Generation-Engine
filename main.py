"""
Automated Lead Generation & Outreach Engine
Entry point: run `python main.py` and follow the prompts, or pass flags.

    python main.py --category "coffee shops" --city "Austin, TX"
"""
import argparse
from datetime import datetime, timezone

from ai_writer import generate_email
from config import settings
from discovery import search_places
from enrichment import find_email
from logger import get_logger
from outreach import evaluate_lead, simulate_send
from storage import SheetStorage

log = get_logger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated lead generation & outreach engine")
    parser.add_argument("--category", help="Business category, e.g. 'coffee shops'")
    parser.add_argument("--city", help="City, e.g. 'Austin, TX'")
    return parser.parse_args()


def get_inputs() -> tuple[str, str]:
    args = parse_args()
    category = args.category or input("Business category: ").strip()
    city = args.city or input("City: ").strip()
    if not category or not city:
        raise SystemExit("Both a category and a city are required.")
    return category, city


def run_pipeline(category: str, city: str) -> None:
    log.info("Starting pipeline for '%s' in '%s'", category, city)

    storage = SheetStorage()
    leads = search_places(category, city, max_results=settings.max_leads_per_run)

    if not leads:
        log.warning("No leads found. Check your query or API key/quota.")
        return

    summary = {"queued": 0, "skipped_low_rating": 0, "no_email_found": 0, "ai_generation_failed": 0}

    for lead in leads:
        name = lead["name"]
        rating = lead.get("rating")
        website = lead.get("website")
        log.info("Processing lead: %s (rating=%s, website=%s)", name, rating, bool(website))

        email = find_email(website)
        status, notes = evaluate_lead(email, rating)

        email_body = None
        if status == "eligible":
            email_body = generate_email(
                business_name=name,
                category=category,
                city=city,
                rating=rating,
                has_website=bool(website),
            )
            status, notes = simulate_send(name, email, email_body)

        summary[status] = summary.get(status, 0) + 1

        storage.append_lead(
            name=name,
            address=lead.get("address", ""),
            phone=lead.get("phone"),
            website=website,
            email=email,
            rating=rating,
            status=status,
            notes=notes,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    log.info("Pipeline complete. Summary: %s", summary)


if __name__ == "__main__":
    category_input, city_input = get_inputs()
    run_pipeline(category_input, city_input)
