"""
Streamlit UI for the Automated Lead Generation & Outreach Engine.
Reuses the same pipeline modules as main.py (CLI) -- this file only adds
a browser-based input/progress/results layer on top.

Run with:
    streamlit run streamlit_app.py
"""
from datetime import datetime, timezone

import streamlit as st

from ai_writer import generate_email
from config import settings
from discovery import search_places
from enrichment import find_email
from outreach import evaluate_lead, simulate_send
from storage import SheetStorage

st.set_page_config(page_title="Lead Gen & Outreach Engine", page_icon="📇", layout="centered")

st.title("📇 Automated lead generation & outreach engine")
st.caption(
    "Finds businesses, extracts contact emails, drafts AI-personalized "
    "outreach, and logs results to Google Sheets. No email is actually sent."
)

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        category = st.text_input("Business category", placeholder="e.g. attorney")
    with col2:
        city = st.text_input("City", placeholder="e.g. Karachi")
    max_results = st.slider(
        "Max leads to pull", min_value=5, max_value=50, value=settings.max_leads_per_run
    )
    submitted = st.form_submit_button("Run pipeline", type="primary", use_container_width=True)

if submitted:
    if not category or not city:
        st.error("Please enter both a business category and a city.")
        st.stop()

    status_box = st.status("Starting pipeline...", expanded=True)
    results = []

    try:
        status_box.write("Connecting to Google Sheets...")
        storage = SheetStorage()

        status_box.write(f"Searching for '{category}' in '{city}'...")
        leads = search_places(category, city, max_results=max_results)

        if not leads:
            status_box.update(label="No leads found.", state="error")
            st.warning("No leads found. Check your query, RapidAPI key, or quota.")
            st.stop()

        status_box.write(f"Found {len(leads)} leads. Processing each one...")
        progress = st.progress(0.0)

        for i, lead in enumerate(leads):
            name = lead["name"]
            rating = lead.get("rating")
            website = lead.get("website")

            status_box.write(f"Processing: **{name}**")

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

            results.append(
                {
                    "name": name,
                    "rating": rating,
                    "website": website,
                    "email": email,
                    "status": status,
                    "email_body": email_body,
                }
            )
            progress.progress((i + 1) / len(leads))

        status_box.update(label="Pipeline complete", state="complete")

    except Exception as exc:  # surfaced in the UI instead of a bare traceback
        status_box.update(label="Pipeline failed", state="error")
        st.error(f"Something went wrong: {exc}")
        st.stop()

    # --- Summary ---
    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1

    st.subheader("Summary")
    cols = st.columns(len(summary) or 1)
    for col, (status, count) in zip(cols, summary.items()):
        col.metric(status.replace("_", " ").title(), count)

    # --- Per-lead results ---
    st.subheader("Leads")
    for r in results:
        with st.expander(f"{r['name']} — {r['status']}"):
            st.write(f"**Rating:** {r['rating'] if r['rating'] is not None else 'n/a'}")
            st.write(f"**Website:** {r['website'] or 'not found'}")
            st.write(f"**Email:** {r['email'] or 'not found'}")
            if r["email_body"]:
                st.text_area("AI-generated outreach email", r["email_body"], height=150, key=r["name"])

    st.success("All leads written to your Google Sheet.")
