Automated Lead Generation & Outreach Engine

A pipeline that takes a business category + city, finds matching businesses via the Google Places API, tries to find each one's contact email by scraping their website, stores everything in a Google Sheet, drafts a personalized outreach email with an LLM, and logs a simulated send outcome for every lead.

No real emails are sent — the "outreach" step is a simulation that decides whether a lead is eligible and logs what would have happened.

Pipeline
Input (CLI) → Google Places search → Website email scrape →
Google Sheets write → AI email draft → Simulated send + log

Each stage lives in its own module so it can be tested and explained independently:

Module	Responsibility
main.py	CLI entry point, orchestrates the pipeline
streamlit_app.py	Streamlit UI entry point (same pipeline, browser front end)
config.py	Loads and validates environment variables
discovery.py	RapidAPI (Google Maps Extractor by FlyByAPIs)
enrichment.py	Scrapes business websites for a contact email
storage.py	Writes leads to Google Sheets via gspread
ai_writer.py	Calls the Groq API to draft outreach emails
outreach.py	Eligibility rules + simulated send
logger.py	Shared console + file logging
Setup
1. Install dependencies
bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. RapidAPI — Google Maps Extractor
Go to the Google Maps Extractor API on RapidAPI and subscribe to the free tier.
Copy your X-RapidAPI-Key from the "Endpoints" tab (it's the same key for every RapidAPI subscription you have).
Note the X-RapidAPI-Host shown on the same page (defaults to google-maps-extractor2.p.rapidapi.com).
Before running the pipeline, click "Test Endpoint" on /locate_and_search with a sample query and check the returned JSON field names against FIELD_CANDIDATES in discovery.py. RapidAPI listings occasionally use different key names than documented — the code tries several common ones, but you may need to add the exact key you see.
Put your key and host in .env as RAPIDAPI_KEY and RAPIDAPI_HOST.
3. Google Sheets
In the same Cloud project, enable the Google Sheets API.
Create a Service Account, then create a JSON key for it and download it.
Save the JSON file somewhere local, e.g. ./credentials/service_account.json.
Create a Google Sheet, and share it with the service account's email address (found inside the JSON file, looks like xxx@yyy.iam.gserviceaccount.com) with Editor access.
Copy the Sheet ID from its URL: https://docs.google.com/spreadsheets/d/<THIS_PART>/edit
4. Groq API key

Get a free key from the Groq Console and set GROQ_API_KEY.

5. Environment variables
bash
cp .env.example .env

Fill in every value in .env:

Variable	Description
RAPIDAPI_KEY	RapidAPI key (from your RapidAPI account)
RAPIDAPI_HOST	RapidAPI host for this API (google-maps-extractor2.p.rapidapi.com)
GOOGLE_SHEETS_CREDENTIALS_PATH	Path to the service account JSON file
GOOGLE_SHEET_ID	Target spreadsheet ID
GROQ_API_KEY	Groq API key
GROQ_MODEL	Model name (defaults to llama-3.3-70b-versatile)
MIN_RATING_THRESHOLD	Leads below this rating are skipped (default 3.5)
MAX_LEADS_PER_RUN	Cap on leads pulled per run (default 20)
REQUEST_TIMEOUT_SECONDS	HTTP timeout for Places/website requests (default 8)

.env is gitignored — never commit real keys.

Running it

Option A — CLI

bash
python main.py --category "coffee shops" --city "Austin, TX"

Or run it interactively and it'll prompt you:

bash
python main.py

Option B — Streamlit UI

bash
streamlit run streamlit_app.py

Opens a browser form for category + city, shows live progress per lead, and displays a per-lead summary (rating, website, email, AI-generated outreach text) after the run — good for the assessment's demo video.

The UI uses a custom khaki + blue color theme defined in .streamlit/config.toml. Edit the hex values there to change it.

Both options use the exact same pipeline modules (discovery.py, enrichment.py, storage.py, ai_writer.py, outreach.py) — the UI is just a different front end over the same logic.

Console output shows progress per lead; a run log is also written to logs/run_<timestamp>.log. Results land as rows in the leads worksheet of your configured Google Sheet, with a status column showing one of:

Status	Meaning
queued	Email drafted and simulated as sent
skipped_low_rating	Rating below MIN_RATING_THRESHOLD
no_email_found	Website had no discoverable email
ai_generation_failed	LLM call failed
Known limitations
The Places extractor does not always return an email address — emails are best-effort, scraped from the business's homepage/contact page, and will sometimes come back empty for sites that use contact forms instead of a listed address.
Website scraping is a single-threaded, timeout-bounded pass over a handful of likely paths (/, /contact, /contact-us, /about) — it's not a full crawler.
This is a simulation: no email is ever actually sent.
Project structure
lead_gen_engine/
├── .streamlit/
│   └── config.toml
├── main.py
├── streamlit_app.py
├── config.py
├── discovery.py
├── enrichment.py
├── storage.py
├── ai_writer.py
├── outreach.py
├── logger.py
├── requirements.txt
├── .env.example
└── README.md
