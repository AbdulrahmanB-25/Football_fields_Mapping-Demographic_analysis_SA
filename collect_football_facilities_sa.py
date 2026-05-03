"""
Saudi Arabia Football Facility Data Collection Script
======================================================
Queries Google Places API for all football-related facilities across Saudi Arabia's
13 administrative regions and inserts results into Supabase via the REST API.

Usage:
    pip install requests
    export GOOGLE_PLACES_API_KEY="your_key_here"
    python collect_football_facilities_sa.py
    python collect_football_facilities_sa.py --details   # also fetches phone + website
"""

import os
import time
import logging
import requests
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
import sys
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[_stream_handler, logging.FileHandler("collection.log", encoding="utf-8")],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "YOUR_API_KEY_HERE")

SUPABASE_URL  = "https://hdcqusmfyovcvtdlawbm.supabase.co"
SUPABASE_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkY3F1c21meW92Y3Z0ZGxhd2JtIiwic"
    "m9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc4OTI5NiwiZXhwIjoyMDkyMzY"
    "1Mjk2fQ.Kn9hL9kAgdpVUvNVq1YjgmOrX1tf33Ke1SfLvUBlnyA"
)
SUPABASE_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=ignore-duplicates,return=minimal",
}

SLEEP_BETWEEN_REQUESTS = 0.8
SLEEP_BETWEEN_CITIES   = 2.0
MAX_PAGES_PER_QUERY    = 3

SOURCE     = "google_places"
CONFIDENCE = 0.85

# ---------------------------------------------------------------------------
# Saudi Arabia: 13 regions + cities
# ---------------------------------------------------------------------------
REGIONS = [
    {
        "name_ar": "منطقة الرياض",
        "name_en": "Riyadh Region",
        "cities": [
            {"name_ar": "الرياض",        "name_en": "Riyadh",        "lat": 24.7136, "lng": 46.6753, "radius": 30000},
            {"name_ar": "الخرج",         "name_en": "Al Kharj",      "lat": 24.1541, "lng": 47.3035, "radius": 10000},
            {"name_ar": "الدوادمي",      "name_en": "Dawadmi",       "lat": 24.5001, "lng": 44.3978, "radius": 8000},
            {"name_ar": "المجمعة",       "name_en": "Majmaah",       "lat": 25.8885, "lng": 45.3557, "radius": 8000},
            {"name_ar": "الزلفي",        "name_en": "Zulfi",         "lat": 26.3065, "lng": 44.8043, "radius": 6000},
            {"name_ar": "شقراء",         "name_en": "Shaqra",        "lat": 25.2437, "lng": 45.2469, "radius": 6000},
            {"name_ar": "وادي الدواسر",  "name_en": "Wadi Dawasir",  "lat": 20.4836, "lng": 45.0099, "radius": 8000},
        ],
    },
    {
        "name_ar": "منطقة مكة المكرمة",
        "name_en": "Makkah Region",
        "cities": [
            {"name_ar": "جدة",           "name_en": "Jeddah",        "lat": 21.5433, "lng": 39.1728, "radius": 25000},
            {"name_ar": "مكة المكرمة",   "name_en": "Makkah",        "lat": 21.3891, "lng": 39.8579, "radius": 15000},
            {"name_ar": "الطائف",        "name_en": "Taif",          "lat": 21.2703, "lng": 40.4158, "radius": 12000},
            {"name_ar": "القنفذة",       "name_en": "Qunfudhah",     "lat": 19.1265, "lng": 41.0786, "radius": 6000},
            {"name_ar": "رابغ",          "name_en": "Rabigh",        "lat": 22.7948, "lng": 39.0344, "radius": 6000},
        ],
    },
    {
        "name_ar": "المنطقة الشرقية",
        "name_en": "Eastern Region",
        "cities": [
            {"name_ar": "الدمام",        "name_en": "Dammam",        "lat": 26.4207, "lng": 50.0888, "radius": 15000},
            {"name_ar": "الخبر",         "name_en": "Khobar",        "lat": 26.2172, "lng": 50.1971, "radius": 10000},
            {"name_ar": "الظهران",       "name_en": "Dhahran",       "lat": 26.2835, "lng": 50.1493, "radius": 8000},
            {"name_ar": "الأحساء",       "name_en": "Al Ahsa",       "lat": 25.3741, "lng": 49.5862, "radius": 15000},
            {"name_ar": "القطيف",        "name_en": "Qatif",         "lat": 26.5227, "lng": 50.0063, "radius": 8000},
            {"name_ar": "حفر الباطن",    "name_en": "Hafar al Batin","lat": 28.4320, "lng": 45.9594, "radius": 8000},
            {"name_ar": "الجبيل",        "name_en": "Jubail",        "lat": 27.0046, "lng": 49.6586, "radius": 8000},
        ],
    },
    {
        "name_ar": "منطقة المدينة المنورة",
        "name_en": "Madinah Region",
        "cities": [
            {"name_ar": "المدينة المنورة","name_en": "Madinah",      "lat": 24.4672, "lng": 39.6151, "radius": 15000},
            {"name_ar": "ينبع",          "name_en": "Yanbu",         "lat": 24.0895, "lng": 38.0618, "radius": 8000},
            {"name_ar": "بدر",           "name_en": "Badr",          "lat": 23.7862, "lng": 38.7825, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة القصيم",
        "name_en": "Qassim Region",
        "cities": [
            {"name_ar": "بريدة",         "name_en": "Buraidah",      "lat": 26.3260, "lng": 43.9750, "radius": 12000},
            {"name_ar": "عنيزة",         "name_en": "Unaizah",       "lat": 26.0846, "lng": 43.9928, "radius": 8000},
            {"name_ar": "الرس",          "name_en": "Ar Rass",       "lat": 25.8623, "lng": 43.4980, "radius": 6000},
        ],
    },
    {
        "name_ar": "منطقة عسير",
        "name_en": "Aseer Region",
        "cities": [
            {"name_ar": "أبها",          "name_en": "Abha",          "lat": 18.2165, "lng": 42.5053, "radius": 10000},
            {"name_ar": "خميس مشيط",    "name_en": "Khamis Mushait","lat": 18.2999, "lng": 42.7300, "radius": 10000},
            {"name_ar": "بيشة",          "name_en": "Bisha",         "lat": 19.9942, "lng": 42.5997, "radius": 6000},
            {"name_ar": "النماص",        "name_en": "An Namas",      "lat": 19.1218, "lng": 42.1292, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة تبوك",
        "name_en": "Tabuk Region",
        "cities": [
            {"name_ar": "تبوك",          "name_en": "Tabuk",         "lat": 28.3838, "lng": 36.5552, "radius": 12000},
            {"name_ar": "تيماء",         "name_en": "Tayma",         "lat": 27.6240, "lng": 38.5429, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة حائل",
        "name_en": "Hail Region",
        "cities": [
            {"name_ar": "حائل",          "name_en": "Hail",          "lat": 27.5219, "lng": 41.6902, "radius": 10000},
            {"name_ar": "بقعاء",         "name_en": "Baq'a",         "lat": 29.0186, "lng": 42.8319, "radius": 4000},
        ],
    },
    {
        "name_ar": "منطقة الحدود الشمالية",
        "name_en": "Northern Borders Region",
        "cities": [
            {"name_ar": "عرعر",          "name_en": "Arar",          "lat": 30.9752, "lng": 41.0381, "radius": 8000},
            {"name_ar": "رفحاء",         "name_en": "Rafha",         "lat": 29.6248, "lng": 43.4913, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة جازان",
        "name_en": "Jizan Region",
        "cities": [
            {"name_ar": "جازان",         "name_en": "Jizan",         "lat": 16.8894, "lng": 42.5511, "radius": 8000},
            {"name_ar": "صبيا",          "name_en": "Sabya",         "lat": 17.1484, "lng": 42.6277, "radius": 5000},
            {"name_ar": "أبو عريش",      "name_en": "Abu Arish",     "lat": 16.9750, "lng": 42.7333, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة نجران",
        "name_en": "Najran Region",
        "cities": [
            {"name_ar": "نجران",         "name_en": "Najran",        "lat": 17.5656, "lng": 44.2289, "radius": 10000},
            {"name_ar": "شرورة",         "name_en": "Sharurah",      "lat": 17.5089, "lng": 47.1247, "radius": 5000},
        ],
    },
    {
        "name_ar": "منطقة الباحة",
        "name_en": "Al-Baha Region",
        "cities": [
            {"name_ar": "الباحة",        "name_en": "Al Baha",       "lat": 20.0126, "lng": 41.4677, "radius": 8000},
            {"name_ar": "بلجرشي",        "name_en": "Baljurashi",    "lat": 20.0928, "lng": 41.5499, "radius": 4000},
        ],
    },
    {
        "name_ar": "منطقة الجوف",
        "name_en": "Al-Jouf Region",
        "cities": [
            {"name_ar": "سكاكا",          "name_en": "Sakaka",        "lat": 29.9697, "lng": 40.2064, "radius": 8000},
            {"name_ar": "دومة الجندل",    "name_en": "Dumat al Jandal","lat": 29.8124,"lng": 39.8699, "radius": 5000},
        ],
    },
]

SEARCH_TERMS = [
    "ملعب كرة قدم",
    "أكاديمية كرة قدم",
    "نادي كرة قدم",
    "ملاعب كرة قدم",
    "صالة كرة قدم",
    "استاد كرة قدم",
    "football academy",
    "football pitch",
    "football stadium",
    "soccer field",
    "sports club football",
    "five-a-side football",
    "padel football",
]

FACILITY_TYPE_MAP = {
    "stadium":          ["استاد", "ملعب رئيسي", "stadium"],
    "football_academy": ["أكاديمية", "academy"],
    "football_club":    ["نادي", "club"],
    "indoor_pitch":     ["صالة", "indoor", "futsal", "صالات"],
    "outdoor_pitch":    ["ملعب", "pitch", "field", "ground"],
    "sports_complex":   ["مركز", "complex", "centre", "مجمع"],
}


def classify_facility(name: str, types: list) -> str:
    combined = (name + " " + " ".join(types)).lower()
    for ftype, keywords in FACILITY_TYPE_MAP.items():
        if any(kw.lower() in combined for kw in keywords):
            return ftype
    return "football_venue"


# ---------------------------------------------------------------------------
# Supabase REST API
# ---------------------------------------------------------------------------
def upsert_facilities(rows: list) -> int:
    if not rows:
        return 0
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/facilities",
        headers=SUPABASE_HEADERS,
        json=rows,
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        log.error("Supabase error %s: %s", resp.status_code, resp.text[:300])
        resp.raise_for_status()
    return len(rows)


# ---------------------------------------------------------------------------
# Google Places API
# ---------------------------------------------------------------------------
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
NEARBY_URL      = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL     = "https://maps.googleapis.com/maps/api/place/details/json"


def _gget(url, params) -> dict:
    params["key"] = GOOGLE_API_KEY
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def text_search(query: str, lat: float, lng: float, radius: int) -> list:
    results = []
    params = {"query": query, "location": f"{lat},{lng}", "radius": radius, "language": "ar"}
    for _ in range(MAX_PAGES_PER_QUERY):
        data = _gget(TEXT_SEARCH_URL, params)
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            break
        results.extend(data.get("results", []))
        token = data.get("next_page_token")
        if not token:
            break
        time.sleep(2)
        params = {"pagetoken": token}
    return results


def nearby_search(keyword: str, lat: float, lng: float, radius: int) -> list:
    results = []
    params = {"keyword": keyword, "location": f"{lat},{lng}", "radius": radius,
              "type": "stadium", "language": "ar"}
    for _ in range(MAX_PAGES_PER_QUERY):
        data = _gget(NEARBY_URL, params)
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            break
        results.extend(data.get("results", []))
        token = data.get("next_page_token")
        if not token:
            break
        time.sleep(2)
        params = {"pagetoken": token}
    return results


def get_place_details(place_id: str) -> dict:
    data = _gget(DETAILS_URL, {"place_id": place_id,
                                "fields": "formatted_phone_number,website",
                                "language": "ar"})
    r = data.get("result", {})
    return {"phone": r.get("formatted_phone_number"), "website": r.get("website")}


def parse_place(raw: dict, city: dict, region: dict) -> Optional[dict]:
    place_id = raw.get("place_id")
    if not place_id:
        return None
    geo = raw.get("geometry", {}).get("location", {})
    return {
        "name_en":             raw.get("name", ""),
        "name_ar":             raw.get("name", ""),
        "facility_type":       classify_facility(raw.get("name", ""), raw.get("types", [])),
        "latitude":            geo.get("lat"),
        "longitude":           geo.get("lng"),
        "city_id":             city["name_en"].replace(" ", "_").lower(),
        "region_id":           region["name_en"].replace(" ", "_").lower(),
        "google_place_id":     place_id,
        "google_rating":       raw.get("rating"),
        "google_reviews_count": raw.get("user_ratings_total"),
        "phone":               None,
        "website":             None,
        "source":              SOURCE,
        "confidence":          CONFIDENCE,
    }


# ---------------------------------------------------------------------------
# Main collection loop
# ---------------------------------------------------------------------------
def collect(fetch_details: bool = False):
    seen_ids: set = set()
    total_inserted = 0

    for region in REGIONS:
        log.info("-- Region: %s", region["name_en"])

        for city in region["cities"]:
            log.info("   City: %s", city["name_en"])
            city_batch = []

            for term in SEARCH_TERMS:
                try:
                    raw_results = text_search(
                        query=f"{term} {city['name_ar']}",
                        lat=city["lat"], lng=city["lng"], radius=city["radius"],
                    )
                    time.sleep(SLEEP_BETWEEN_REQUESTS)

                    raw_results += nearby_search(
                        keyword=term,
                        lat=city["lat"], lng=city["lng"], radius=city["radius"],
                    )
                    time.sleep(SLEEP_BETWEEN_REQUESTS)

                    for raw in raw_results:
                        pid = raw.get("place_id")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            row = parse_place(raw, city, region)
                            if row:
                                city_batch.append(row)

                except requests.RequestException as exc:
                    log.error("Request error for %r in %s: %s", term, city["name_en"], exc)
                    time.sleep(5)

            if fetch_details and city_batch:
                log.info("   Fetching details for %d places…", len(city_batch))
                for row in city_batch:
                    try:
                        row.update(get_place_details(row["google_place_id"]))
                        time.sleep(SLEEP_BETWEEN_REQUESTS)
                    except requests.RequestException as exc:
                        log.warning("Details error %s: %s", row["google_place_id"], exc)

            inserted = upsert_facilities(city_batch)
            total_inserted += inserted
            log.info("   [OK] %d rows sent (batch %d)", inserted, len(city_batch))
            time.sleep(SLEEP_BETWEEN_CITIES)

    log.info("Done. Total rows sent: %d", total_inserted)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect Saudi football facilities")
    parser.add_argument("--details", action="store_true",
                        help="Fetch phone + website per facility (uses extra API quota)")
    args = parser.parse_args()

    if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        log.error("Set GOOGLE_PLACES_API_KEY environment variable before running.")
        raise SystemExit(1)

    collect(fetch_details=args.details)
