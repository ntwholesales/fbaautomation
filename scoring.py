"""
Turns raw Keepa product stats into a single 0-100 "opportunity score" plus
the underlying fields, so you can re-sort/filter in a spreadsheet however
you like. This is a demand/competition heuristic, NOT a margin calculation
(we don't know your supplier cost yet).

Adjust the weights in `score_product` once you've seen real output and have
a feel for what predicts a good sourcing lead for you.
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
    """
    Higher score = more attractive to look into further.
    Rewards: better (lower) sales rank, fewer competing offers, higher
    rating, more reviews (proven demand). Penalizes Amazon itself selling
    the listing (much harder to win the buy box against Amazon directly).
    """
    score = 0.0

    if fields["sales_rank"]:
        # Lower rank is better; compress with a log-ish curve.
        score += max(0, 100 - (fields["sales_rank"] / 1000))

    if fields["offer_count"] is not None:
        score += max(0, 20 - fields["offer_count"])  # fewer sellers = better

    if fields["rating"] is not None:
        score += fields["rating"] * 5  # up to 25 pts

    if fields["review_count"] is not None:
        score += min(20, fields["review_count"] / 50)  # diminishing returns

    if fields["amazon_sells_it"]:
        score -= 30  # hard to compete directly against Amazon on its own listing

    return round(score, 2)
