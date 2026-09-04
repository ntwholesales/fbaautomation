"""
Daily scan entry point.

    python3 main.py

Loops through config.BRANDS, queries Keepa for candidates, scores them,
and writes output/candidates_<date>.csv with the top results.
"""

import csv
import datetime
import os
import sys

import config
from keepa_client import KeepaClient, KeepaError
from scoring import extract_fields, passes_filters, score_product

FIELDNAMES = [
    "score",
    "brand",
    "asin",
    "title",
    "sales_rank",
    "offer_count",
    "rating",
    "review_count",
    "price_usd",
    "amazon_sells_it",
    "amazon_url",
]


def run():
    try:
        client = KeepaClient(api_key=config.KEEPA_API_KEY, domain=config.DOMAIN)
    except KeepaError as e:
        print(f"Setup error: {e}", file=sys.stderr)
        sys.exit(1)

    all_candidates = []

    for brand in config.BRANDS:
        print(f"Scanning brand: {brand} ...")
        try:
            asins = client.find_asins_by_brand(
                brand,
                max_sales_rank=config.MAX_SALES_RANK,
                per_page=config.RESULTS_PER_BRAND,
            )
        except KeepaError as e:
            print(f"  Skipping {brand} — Product Finder error: {e}", file=sys.stderr)
            continue

        if not asins:
            print(f"  No results for {brand}.")
            continue

        print(f"  {len(asins)} ASIN(s) found, fetching stats...")
        try:
            products = client.get_product_stats(asins)
        except KeepaError as e:
            print(f"  Skipping {brand} — stats fetch error: {e}", file=sys.stderr)
            continue

        for product in products:
            fields = extract_fields(product, brand)
            if not passes_filters(fields, config):
                continue
            fields["score"] = score_product(fields)
            all_candidates.append(fields)

    if not all_candidates:
        print("No candidates passed the filters today. Try loosening config.py thresholds.")
        return

    all_candidates.sort(key=lambda f: f["score"], reverse=True)
    top = all_candidates[: config.TOP_N_RESULTS]

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    out_path = os.path.join(config.OUTPUT_DIR, f"candidates_{today}.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in top:
            writer.writerow(row)

    print(f"\nWrote {len(top)} candidates to {out_path}\n")
    print("Top 10:")
    for row in top[:10]:
        print(
            f"  [{row['score']:>6}] {row['brand']:<12} {row['title'][:60]:<60} "
            f"rank={row['sales_rank']} offers={row['offer_count']} "
            f"rating={row['rating']} ${row['price_usd']}"
        )


if __name__ == "__main__":
    run()
