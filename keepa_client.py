"""
Thin wrapper around Keepa's raw HTTP API (no third-party keepa package
dependency, so it's easy to see exactly what's being sent/received).

Two endpoints used:
  - POST /query   -> Product Finder: brand/category/rank filters -> ASIN list
  - GET  /product -> full stats for a batch of ASINs
"""

import json
import time
import requests

from constants import KEEPA_QUERY_URL, KEEPA_PRODUCT_URL


class KeepaError(Exception):
    pass


class KeepaClient:
    def __init__(self, api_key: str, domain: int = 1, timeout: int = 30):
        if not api_key:
            raise KeepaError(
                "No Keepa API key found. Set KEEPA_API_KEY in your .env file."
            )
        self.api_key = api_key
        self.domain = domain
        self.timeout = timeout

    def find_asins_by_brand(
        self, brand: str, max_sales_rank: int, per_page: int = 50
    ) -> list[str]:
        """Query Keepa's Product Finder for ASINs matching a brand."""
        selection = {
            "brand": [brand],
            "current_SALES_gte": 1,
            "current_SALES_lte": max_sales_rank,
            "sort": [["current_SALES", "asc"]],
            "perPage": per_page,
            "page": 0,
        }
        params = {"key": self.api_key, "domain": self.domain}
        body = {"selection": json.dumps(selection)}

        resp = requests.post(
            KEEPA_QUERY_URL, params=params, json=body, timeout=self.timeout
        )
        self._raise_for_status(resp)
        data = resp.json()
        return data.get("asinList", []) or []

    def get_product_stats(
        self, asins: list[str], stats_days: int = 180
    ) -> list[dict]:
        """Fetch full stats for a batch of ASINs (Keepa allows up to 100/call)."""
        products = []
        batch_size = 100
        for i in range(0, len(asins), batch_size):
            batch = asins[i : i + batch_size]
            params = {
                "key": self.api_key,
                "domain": self.domain,
                "asin": ",".join(batch),
                "stats": stats_days,
                "offers": 20,
                "rating": 1,
            }
            resp = requests.get(KEEPA_PRODUCT_URL, params=params, timeout=self.timeout)
            self._raise_for_status(resp)
            data = resp.json()
            products.extend(data.get("products", []) or [])
            time.sleep(1)  # be gentle on the token bucket between batches
        return products

    @staticmethod
    def _raise_for_status(resp: requests.Response):
        if resp.status_code != 200:
            raise KeepaError(
                f"Keepa API error {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()
        if "error" in data and data["error"]:
            raise KeepaError(f"Keepa API returned an error: {data['error']}")
