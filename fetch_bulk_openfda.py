"""
fetch_bulk_openfda.py — Scale-up script (Owner: Rameen)

WHAT THIS DOES (different from fetch_openfda.py):
The original script needed a LIST of 20 medicine names to search for.
This script instead pulls records DIRECTLY from OpenFDA's drug label
database in bulk pages — no name list needed — so it can scale to
hundreds of medicines quickly.

RESUMABLE: saves progress after every page to data/bulk_medicines.json.
If your internet drops halfway, just run it again — it picks up where
it left off instead of starting over.

HOW TO RUN:
    python fetch_bulk_openfda.py

You can stop it anytime with Ctrl+C — whatever it already saved stays.
"""

import json
import os
import time
import urllib.request
import urllib.parse

OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "bulk_medicines.json")
OPENFDA_URL = "https://api.fda.gov/drug/label.json"

PAGE_SIZE = 99          # OpenFDA's max allowed per request
TARGET_COUNT = 1000     # aspirational ceiling — script is resumable, so stop early with Ctrl+C anytime and keep whatever was fetched
MAX_PAGES = 150         # hard safety cap so this can't run forever


def _load_existing():
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(data):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _fetch_page(skip: int) -> list:
    params = {"limit": PAGE_SIZE, "skip": skip}
    url = OPENFDA_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])
    except Exception as e:
        print(f"  [!] Page at skip={skip} failed: {e} — retrying once...")
        time.sleep(2)
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
        except Exception as e2:
            print(f"  [!] Retry also failed: {e2} — skipping this page.")
            return []


def _record_from_result(r: dict, next_id: int) -> dict:
    openfda = r.get("openfda", {})
    name = (openfda.get("generic_name") or openfda.get("brand_name") or [""])[0]
    if not name:
        return None

    return {
        "id": str(next_id),
        "medicine_name": name.title(),
        "drug_type": ", ".join(openfda.get("pharm_class_epc", []))[:150],
        "main_use": " ".join(r.get("indications_and_usage", [])) or " ".join(r.get("purpose", [])),
        "common_forms": ", ".join(openfda.get("route", [])),
        "safety_note": " ".join(r.get("warnings", []))[:500],
        "source_reference": "OpenFDA (bulk import)",
        "openfda_purpose": " ".join(r.get("purpose", [])),
        "openfda_warnings": " ".join(r.get("warnings", []) or r.get("warnings_and_cautions", [])),
        "openfda_contraindications": " ".join(r.get("do_not_use", []) or r.get("contraindications", [])),
        "openfda_side_effects": " ".join(r.get("adverse_reactions", [])),
    }


def main():
    existing = _load_existing()
    seen_names = {m["medicine_name"].lower() for m in existing}
    next_id = 1000 + len(existing)  # keep IDs separate from the original 20 (1-20)

    print(f"Starting with {len(existing)} medicines already saved.")

    skip = 0
    pages_done = 0

    while len(existing) < TARGET_COUNT and pages_done < MAX_PAGES:
        print(f"Fetching page at skip={skip} ({len(existing)}/{TARGET_COUNT} unique medicines so far)...")
        results = _fetch_page(skip)
        if not results:
            print("No more results returned — stopping.")
            break

        for r in results:
            record = _record_from_result(r, next_id)
            if record and record["medicine_name"].lower() not in seen_names:
                existing.append(record)
                seen_names.add(record["medicine_name"].lower())
                next_id += 1

        _save(existing)  # save after EVERY page — this is what makes it resumable
        skip += PAGE_SIZE
        pages_done += 1
        time.sleep(0.3)  # be polite to the API

    print(f"\nDone. {len(existing)} unique medicines saved to {OUT_PATH}")
    print("Next step: run merge_bulk.py to combine this with your original 20.")


if __name__ == "__main__":
    main()
