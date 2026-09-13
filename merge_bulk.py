"""
merge_bulk.py — Owner: Rameen

Combines your original 20 curated medicines (data/enriched_medicines.json)
with the new bulk-fetched ones (data/bulk_medicines.json) into ONE final
file — this is what build_index.py will actually read.

Run this AFTER fetch_bulk_openfda.py finishes (or after you stop it early
with Ctrl+C — partial progress is fine).

HOW TO RUN:
    python merge_bulk.py
"""

import json
import os

BASE_DIR = os.path.dirname(__file__)
ORIGINAL_PATH = os.path.join(BASE_DIR, "data", "enriched_medicines.json")
BULK_PATH = os.path.join(BASE_DIR, "data", "bulk_medicines.json")
FINAL_PATH = os.path.join(BASE_DIR, "data", "enriched_medicines.json")  # overwrite with combined list


def main():
    with open(ORIGINAL_PATH, encoding="utf-8") as f:
        original = json.load(f)

    if not os.path.exists(BULK_PATH):
        print("No bulk_medicines.json found — run fetch_bulk_openfda.py first.")
        return

    with open(BULK_PATH, encoding="utf-8") as f:
        bulk = json.load(f)

    seen_names = {m["medicine_name"].lower() for m in original}
    added = 0

    for m in bulk:
        if m["medicine_name"].lower() not in seen_names:
            original.append(m)
            seen_names.add(m["medicine_name"].lower())
            added += 1

    with open(FINAL_PATH, "w", encoding="utf-8") as f:
        json.dump(original, f, indent=2, ensure_ascii=False)

    print(f"Merged {added} new medicines from bulk fetch.")
    print(f"Total medicines now: {len(original)}")
    print(f"Saved to {FINAL_PATH} — now run: python build_index.py")


if __name__ == "__main__":
    main()
