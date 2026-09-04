"""
Central config. Edit BRANDS and the thresholds below to tune what the
scanner looks for. Everything here is a plain Python value on purpose —
no need to touch other files to adjust your search.
"""

import os
from dotenv import load_dotenv

load_dotenv()

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY", "")

# Amazon marketplace domain id used by Keepa. 1 = amazon.com (US).
# Others: 2=UK, 3=DE, 4=FR, 5=JP, 6=CA, 8=IT, 9=ES, 10=IN, 11=MX, 12=BR, 13=AU
DOMAIN = 1

# Brands to scan. Keepa's brand filter uses OR logic across a list, but we
# query one brand at a time so the CSV output tells you which brand each
# result came from.
BRANDS = [
    "Philips",
    "LEGO",
    "Remington",
    # add more beauty/brand names here, e.g.:
    # "Revlon",
    # "CeraVe",
    # "Conair",
]

# --- Product Finder filters (applied when searching, cheap in tokens) ---

# Only consider products selling reasonably well (lower sales rank = better).
# 100,000 is a loose starting filter for most categories; tighten later.
MAX_SALES_RANK = 100_000

# Max results to pull per brand per run (Keepa allows up to 10,000 but you
# don't need that many — start small while you tune scoring).
RESULTS_PER_BRAND = 50

# --- Post-fetch filters (applied after pulling full stats) ---

MAX_OFFER_COUNT = 15        # skip products with heavy seller competition
MIN_RATING = 3.8            # out of 5
MIN_REVIEWS = 20            # minimum review count, filters out brand-new junk

# How many top-scoring candidates to keep in the final CSV, across all brands
TOP_N_RESULTS = 100

OUTPUT_DIR = "output"
