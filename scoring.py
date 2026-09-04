"""Turn raw Keepa statistics into a 0-100 opportunity score.

The score is a demand/competition heuristic, not a margin calculation:
supplier cost, Amazon fees, and eligibility still need separate checks.
"""

from constants import CSV_TYPE

NO_DATA = -1


def _csv_val(arr, key):
    """Safely pull a value out of a Keepa CSV-indexed array."""
    idx = CSV_TYPE[key]
    if not arr or len(arr) <= idx:
        return None
    val = arr[idx]
    return None if val == NO_DATA else val


def extract_fields(product: dict, brand: str) -> dict:
    """Pull the fields we care about out of a raw Keepa product object."""
    stats = product.get("stats") or {}
    current = stats.get("current") or []

    sales_rank = _csv_val(current, "SALES")
    offer_count = _csv_val(current, "COUNT_NEW")
    rating_raw = _csv_val(current, "RATING")
    review_count = _csv_val(current, "COUNT_REVIEWS")
    price_new = _csv_val(current, "NEW")  # cents
    amazon_price = _csv_val(current, "AMAZON")  # cents; present if Amazon sells it

    return {
        "asin": product.get("asin"),
        "brand": brand,
        "title": (product.get("title") or "")[:120],
        "sales_rank": sales_rank,
        "offer_count": offer_count,
        "rating": (rating_raw / 10) if rating_raw is not None else None,
        "review_count": review_count,
        "price_usd": (price_new / 100) if price_new is not None else None,
        "amazon_sells_it": amazon_price is not None,
        "amazon_url": f"https://www.amazon.com/dp/{product.get('asin')}",
    }


def passes_filters(fields: dict, cfg) -> bool:
    if fields["sales_rank"] is None or fields["sales_rank"] > cfg.MAX_SALES_RANK:
        return False
    if fields["offer_count"] is not None and fields["offer_count"] > cfg.MAX_OFFER_COUNT:
        return False
    if fields["rating"] is not None and fields["rating"] < cfg.MIN_RATING:
        return False
    if fields["review_count"] is not None and fields["review_count"] < cfg.MIN_REVIEWS:
        return False
    return True


def score_product(fields: dict) -> float:
    """Return a 0-100 score; higher means a more promising lead."""
    score = 0.0

    if fields["sales_rank"] is not None:
        # Lower rank is better. Products at rank 100,000 or worse earn zero.
        score += max(0, 50 - (fields["sales_rank"] / 2_000))

    if fields["offer_count"] is not None:
        score += max(0, 20 - fields["offer_count"])

    if fields["rating"] is not None:
        score += min(20, fields["rating"] * 4)

    if fields["review_count"] is not None:
        score += min(10, fields["review_count"] / 100)

    if fields["amazon_sells_it"]:
        score -= 20

    return round(max(0, min(100, score)), 2)
