"""Thin wrapper around Keepa's raw HTTP API.

Two endpoints used:
  - POST /query   -> Product Finder: brand/category/rank filters -> ASIN list
  - GET  /product -> stats for a batch of ASINs
"""

import json
import time

import requests

from constants import KEEPA_PRODUCT_URL, KEEPA_QUERY_URL


class KeepaError(Exception):
    """An API or connection error that the scanner can report cleanly."""


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
        if not 50 <= per_page <= 10_000:
            raise KeepaError("per_page must be between 50 and 10,000.")
        if max_sales_rank < 1:
            raise KeepaError("max_sales_rank must be at least 1.")

        selection = {
            "brand": [brand],
            "current_SALES_gte": 1,
            "current_SALES_lte": max_sales_rank,
            "sort": [["current_SALES", "asc"]],
            "perPage": per_page,
            "page": 0,
        }
        data = self._request_json(
            requests.post,
            KEEPA_QUERY_URL,
            params={"key": self.api_key, "domain": self.domain},
            # For POST, Keepa expects the selection JSON itself as the body.
            json=selection,
        )
        return data.get("asinList", []) or []

    def get_product_stats(
        self, asins: list[str], stats_days: int = 180
    ) -> list[dict]:
        """Fetch current statistics for ASINs in batches of at most 100."""
        if not asins:
            return []
        if stats_days < 1:
            raise KeepaError("stats_days must be at least 1.")

        products = []
        batch_size = 100
        for i in range(0, len(asins), batch_size):
            batch = asins[i : i + batch_size]
            data = self._request_json(
                requests.get,
                KEEPA_PRODUCT_URL,
                params={
                    "key": self.api_key,
                    "domain": self.domain,
                    "asin": ",".join(batch),
                    "stats": stats_days,
                    # Adds rating and review fields without paying for offer pages.
                    "rating": 1,
                },
            )
            products.extend(data.get("products", []) or [])
            if i + batch_size < len(asins):
                time.sleep(1)  # be gentle on the token bucket between batches
        return products

    def _request_json(self, request, url: str, **kwargs) -> dict:
        try:
            response = request(url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise KeepaError(f"Could not reach Keepa: {exc}") from exc

        if response.status_code != 200:
            raise KeepaError(
                f"Keepa API error {response.status_code}: {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise KeepaError("Keepa returned an invalid JSON response.") from exc

        error = data.get("error")
        if error:
            if isinstance(error, dict):
                error = error.get("message") or json.dumps(error)
            raise KeepaError(f"Keepa API returned an error: {error}")
        return data
