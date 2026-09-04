"""
Run this FIRST, before trusting the scoring pipeline:

    python3 debug_inspect.py B0088PUEPK

Prints the raw Keepa /product response for one ASIN so you can visually
confirm the 'stats.current' array lines up with constants.CSV_TYPE. If
Keepa's response shape doesn't match, adjust constants.py accordingly.
"""

import json
import sys

import requests

import config
from constants import KEEPA_PRODUCT_URL


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 debug_inspect.py <ASIN>")
        sys.exit(1)

    asin = sys.argv[1]
    params = {
        "key": config.KEEPA_API_KEY,
        "domain": config.DOMAIN,
        "asin": asin,
        "stats": 180,
        "offers": 20,
        "rating": 1,
    }
    resp = requests.get(KEEPA_PRODUCT_URL, params=params, timeout=30)
    print(f"HTTP {resp.status_code}")
    data = resp.json()

    products = data.get("products") or []
    if not products:
        print("No product returned. Full response:")
        print(json.dumps(data, indent=2)[:3000])
        return

    product = products[0]
    print("Top-level keys:", list(product.keys()))
    print("\nbrand:", product.get("brand"))
    print("title:", product.get("title"))

    stats = product.get("stats") or {}
    print("\nstats keys:", list(stats.keys()))
    print("stats.current (index: value):")
    for i, v in enumerate(stats.get("current", [])):
        print(f"  [{i}] = {v}")


if __name__ == "__main__":
    main()
