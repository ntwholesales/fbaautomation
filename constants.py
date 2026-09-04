"""
Keepa encodes price/rank history as arrays indexed by a fixed "CSV type".
These indices are widely documented and stable, but Keepa has occasionally
added new types at the end of the list over the years, and behavior can
differ slightly by plan/response options requested (stats, offers, buybox).

IMPORTANT: run `python3 debug_inspect.py <ASIN>` and eyeball a real response
before trusting these blindly — see README.md.
"""

CSV_TYPE = {
    "AMAZON": 0,           # Amazon's own price
    "NEW": 1,               # Marketplace new price (lowest, incl. shipping)
    "USED": 2,
    "SALES": 3,             # Sales rank
    "LISTPRICE": 4,
    "COLLECTIBLE": 5,
    "REFURBISHED": 6,
    "NEW_FBM_SHIPPING": 7,
    "LIGHTNING_DEAL": 8,
    "WAREHOUSE": 9,
    "NEW_FBA": 10,
    "COUNT_NEW": 11,        # number of active new offers
    "COUNT_USED": 12,
    "COUNT_REFURBISHED": 13,
    "COUNT_COLLECTIBLE": 14,
    "RATING": 16,           # product rating * 10 (e.g. 45 = 4.5 stars)
    "COUNT_REVIEWS": 17,
}

KEEPA_QUERY_URL = "https://api.keepa.com/query"
KEEPA_PRODUCT_URL = "https://api.keepa.com/product"
