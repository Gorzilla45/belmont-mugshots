"""
Belmont County Mugshot Post Helper
Simple local web app for beginners.
"""

import os
import json
import base64
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

# ---------- SETTINGS ----------
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MUGSHOT_DIR = APP_DIR / "static" / "mugshots"
QUEUE_FILE = DATA_DIR / "queue.json"
SEEN_FILE = DATA_DIR / "seen.json"
ROSTER_URL = "https://www.belmontsheriff.com/bcsojailroster/"

DATA_DIR.mkdir(exist_ok=True)
MUGSHOT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "belmont-local-app-change-me-later"

# ---------- HELPERS ----------
def load_json(path, default=None):
    if default is None:
        default = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def make_id(jail_id, book_date, name):
    raw = f"{jail_id}|{book_date}|{name}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

# ---------- SCRAPER ----------
def scrape_roster():
    """Scrape Belmont County roster. Returns list of new inmates only."""
    print(f"[{datetime.now()}] Scraping roster...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(ROSTER_URL, headers=headers, timeout=45)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    seen = set(load_json(SEEN_FILE, []))
    new_inmates = []

    # Collect all table rows in order
    rows = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        texts = [clean(c.get_text()) for c in cells]
        img = tr.find("img")
        photo_data = None
        if img and img.get("src", "").startswith("data:image"):
            photo_data = img["src"]
        rows.append({"texts": texts, "photo": photo_data})

    i = 0
    while i < len(rows):
        texts = rows[i]["texts"]
        photo = rows[i]["photo"]

        # A new inmate starts with a row that has Jail ID + Name
        # Example: ['200012941', '', 'Ault, Joshua Lee', 'DOMESTIC VIOLENCE', ...]
        if len(texts) >= 3 and re.match(r"^\d{6,}$", texts[0]) and "," in texts[2]:
            jail_id = texts[0]
            name = texts[2]
            charges = []
            if texts[3]:
                charges.append(texts[3])

            book_date = ""
            agency = ""
            photo_data = photo

            # Look ahead for more charges and the Book Date / Agency row
            j = i + 1
            while j < len(rows):
                t = rows[j]["texts"]
                # Charge continuation rows usually start with uppercase charge name
                if len(t) >= 1 and t[0] and t[0][0].isupper() and "Court" in " ".join(t):
                    if t[0] not in ("SID#", "Book Date", "Release Date", "Jail ID"):
                        charges.append(t[0])
                # Book Date row
                if "Book Date" in t:
                    # next row usually has the actual date and agency
                    if j + 1 < len(rows):
                        next_t = rows[j + 1]["texts"]
                        for val in next_t:
                            if re.match(r"\d{2}/\d{2}/\d{4}", val):
                                book_date = val
                            if any(x in val for x in ["Police", "Sheriff", "Department", "Authority", "Probation", "Transport"]):
                                agency = val
                    break
                # Stop if we hit the next inmate header
                if len(t) >= 3 and re.match(r"^\d{6,}$", t[0]) and "," in (t[2] if len(t) > 2 else ""):
                    break
                j += 1

            if not agency:
                agency = "Belmont County Sheriff's Office"
            if not book_date:
                book_date = "Unknown"

            uid = make_id(jail_id, book_date, name)
            if uid not in seen:
                # Save mugshot
                photo_path = None
                if photo_data:
                    try:
                        _, b64data = photo_data.split(",", 1)
                        img_bytes = base64.b64decode(b64data)
                        filename = f"{uid}.jpg"
                        with open(MUGSHOT_DIR / filename, "wb") as f:
                            f.write(img_bytes)
                        photo_path = f"mugshots/{filename}"
                    except Exception as e:
                        print(f"Photo save error for {name}: {e}")

                inmate = {
                    "id": uid,
                    "jail_id": jail_id,
                    "name": name,
                    "charges": charges or ["See public roster"],
                    "book_date": book_date,
                    "agency": agency,
                    "photo": photo_path,
                    "scraped_at": datetime.now().isoformat(),
                }
                new_inmates.append(inmate)
                seen.add(uid)

            i = j
        else:
            i += 1

    save_json(SEEN_FILE, list(seen))
    print(f"Found {len(new_inmates)} new inmates")
    return new_inmates

# ---------- POST GENERATOR ----------
DISCLAIMERS = [
    "This information comes from public records. An arrest is not a conviction. Charges may be reduced or dismissed.",
    "Public record information only. Arrest does not equal guilt. All persons are presumed innocent until proven guilty in a court of law.",
    "Sourced from the Belmont County Sheriff public roster. An arrest is not a conviction.",
]

INTROS = [
    "New booking reported:",
    "Recently booked:",
    "Public roster update:",
    "New entry on the Belmont County jail roster:",
]

def generate_post(inmate):
    import random
    intro = random.choice(INTROS)
    disclaimer = random.choice(DISCLAIMERS)

    name = inmate["name"]
    book_date = inmate["book_date"]
    agency = inmate["agency"]
    charges = inmate["charges"]

    charge_text = ", ".join(charges[:4])
    if len(charges) > 4:
        charge_text += " and others"

    note = ""
    upper = charge_text.upper()
    if "DOMESTIC VIOLENCE" in upper:
        note = " (Domestic violence offense under Ohio law.)"
    elif "DRIVING UNDER THE INFLUENCE" in upper or "DUI" in upper:
        note = " (Operating a vehicle under the influence.)"
    elif "THEFT" in upper:
        note = " (Theft-related offense.)"
    elif "PROBATION" in upper:
        note = " (Probation violation.)"

    post = (
        f"{intro}\n\n"
        f"Name: {name}\n"
        f"Booked: {book_date}\n"
        f"Arresting Agency: {agency}\n"
        f"Charge(s): {charge_text}{note}\n\n"
        f"{disclaimer}"
    )
    return post

# ---------- QUEUE ----------
def add_to_queue(inmate):
    queue = load_json(QUEUE_FILE, [])
    # Avoid duplicates already in queue
    existing_ids = {item["id"] for item in queue}
    if inmate["id"] in existing_ids:
        return None
    post_text = generate_post(inmate)
    item = {
        "id": inmate["id"],
        "inmate": inmate,
        "post_text": post_text,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "status": "pending",
    }
    queue.append(item)
    save_json(QUEUE_FILE, queue)
    return item

def get_active_queue():
    queue = load_json(QUEUE_FILE, [])
    now = datetime.now()
    active = []
    for item in queue:
        try:
            expires = datetime.fromisoformat(item["expires_at"])
            if expires > now and item["status"] in ("pending", "approved"):
                active.append(item)
        except Exception:
            continue
    # newest first
    active.sort(key=lambda x: x["created_at"], reverse=True)
    return active

def update_item_status(item_id, new_status):
    queue = load_json(QUEUE_FILE, [])
    for item in queue:
        if item["id"] == item_id:
            item["status"] = new_status
            break
    save_json(QUEUE_FILE, queue)

# ---------- WEB ROUTES ----------
@app.route("/")
def index():
    active = get_active_queue()
    return render_template("index.html", posts=active)

@app.route("/scrape", methods=["POST"])
def run_scrape():
    new_ones = scrape_roster()
    added = 0
    for inmate in new_ones:
        if add_to_queue(inmate):
            added += 1
    flash(f"Scrape finished. Added {added} new post(s) to the queue.")
    return redirect(url_for("index"))

@app.route("/approve/<item_id>", methods=["POST"])
def approve(item_id):
    update_item_status(item_id, "approved")
    flash("Post marked as approved. Copy the text and photo to Facebook when ready.")
    return redirect(url_for("index"))

@app.route("/discard/<item_id>", methods=["POST"])
def discard(item_id):
    update_item_status(item_id, "discarded")
    flash("Post discarded.")
    return redirect(url_for("index"))

@app.route("/static/mugshots/<path:filename>")
def mugshot(filename):
    return send_from_directory(MUGSHOT_DIR, filename)

# ---------- HOURLY SCHEDULER ----------
def scheduled_scrape():
    try:
        new_ones = scrape_roster()
        for inmate in new_ones:
            add_to_queue(inmate)
    except Exception as e:
        print(f"Scheduled scrape error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_scrape, "interval", hours=1, id="hourly_scrape")
scheduler.start()

# ---------- START ----------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print("=" * 55)
    print("  Belmont County Mugshot Helper")
    print(f"  Running on port {port}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=port, debug=False)
