import requests
import time
import threading
from typing import Dict
from config import PRICE_URL

CACHE_DURATION = 60  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

class PriceCache:
    def __init__(self):
        self.cache: Dict[str, float] = {}
        self.last_fetch: float = 0
        self.last_successful_fetch: float = 0
        self.lock = threading.Lock()
        self.is_fetching = False

    def fetch_prices(self) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(PRICE_URL, timeout=10)
                r.raise_for_status()
                data = r.json()

                new_cache = {
                    "BTC": data.get("bitcoin", {}).get("usd", 0),
                    # "ETH": data.get("ethereum", {}).get("usd", 0),
                }

                if all(price > 0 for price in new_cache.values()):
                    with self.lock:
                        self.cache = new_cache
                        self.last_fetch = time.time()
                        self.last_successful_fetch = time.time()
                    print(f"✓ Prices updated successfully: {new_cache}")
                    return True
                else:
                    print(f"Warning: Received invalid price data (attempt {attempt + 1}/{MAX_RETRIES})")

            except requests.exceptions.Timeout:
                print(f"Timeout fetching prices (attempt {attempt + 1}/{MAX_RETRIES})")
            except requests.exceptions.RequestException as e:
                print(f"Network error fetching prices (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            except (KeyError, ValueError) as e:
                print(f"Error parsing price data (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            except Exception as e:
                print(f"Unexpected error fetching prices (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        with self.lock:
            self.last_fetch = time.time()
        print("✗ Failed to fetch prices after all retries")
        return False

    def get_price(self, chain: str) -> float:
        chain = chain.upper()
        current_time = time.time()

        with self.lock:
            cache_expired = (current_time - self.last_fetch) > CACHE_DURATION
            chain_missing = chain not in self.cache
            should_fetch = (cache_expired or chain_missing) and not self.is_fetching

        if should_fetch:
            with self.lock:
                self.is_fetching = True
            try:
                self.fetch_prices()
            finally:
                with self.lock:
                    self.is_fetching = False

        with self.lock:
            price = self.cache.get(chain, 0)

        if (price > 0 and (current_time - self.last_successful_fetch) > CACHE_DURATION * 2):
            print(f"Warning: Using stale price data for {chain} "f"(last updated {int(current_time - self.last_successful_fetch)}s ago)")

        return price

    def get_all_prices(self) -> Dict[str, float]:
        with self.lock:
            return self.cache.copy()

    def is_cache_valid(self) -> bool:
        with self.lock:
            cache_age = time.time() - self.last_successful_fetch
            has_data = len(self.cache) > 0 and all(p > 0 for p in self.cache.values())
            return has_data and cache_age < CACHE_DURATION * 2

    def force_refresh(self) -> bool:
        with self.lock:
            if self.is_fetching:
                return False
            self.is_fetching = True

        try:
            return self.fetch_prices()
        finally:
            with self.lock:
                self.is_fetching = False

price_cache = PriceCache()
price_cache.fetch_prices()
