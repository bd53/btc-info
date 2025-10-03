import requests
import time

CACHE_DURATION = 60

class PriceCache:
    def __init__(self):
        self.cache = {}
        self.last_fetch = 0

    def fetch_prices(self):
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            self.cache = {
                "BTC": data.get("bitcoin", {}).get("usd", 0),
                "ETH": data.get("ethereum", {}).get("usd", 0),
            }
            self.last_fetch = time.time()
        except Exception as e:
            print("Error fetching prices:", e)

    def get_price(self, chain):
        if time.time() - self.last_fetch > CACHE_DURATION or chain not in self.cache:
            self.fetch_prices()
        return self.cache.get(chain, 0)

price_cache = PriceCache()