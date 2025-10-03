import importlib
import time
from utils.price import price_cache
from config import POLL_INTERVAL, LARGE_TX_THRESHOLD_USD, CHAINS

seen_tx_hashes = set()


def load_chain_handler(name):
    module = importlib.import_module(f"chains.{name}")
    return module


def process_tx(tx, price_usd):
    value_usd = tx["value"] * price_usd
    print(f"[{tx['chain']}] {tx['tx_hash']}")
    print(f"From: {tx['from']}")
    print(f"To: {tx['to']}")
    print(f"Value: {tx['value_str']} (~${value_usd:.2f} USD)")
    print(f"Status: {tx['status']}")
    if value_usd > LARGE_TX_THRESHOLD_USD:
        print("Large transaction detected!")
    print("-" * 40)


def poll_loop():
    chain_handlers = {name: load_chain_handler(name) for name in CHAINS}
    while True:
        for chain, handler in chain_handlers.items():
            price_usd = price_cache.get_price(chain.upper())
            if price_usd == 0:
                print(f"Skipping {chain.upper()} poll due to price fetch failure.")
                continue
            try:
                txs = handler.fetch_unconfirmed_txs()
                for tx_raw in txs:
                    tx = handler.parse_tx(tx_raw)
                    if not tx["tx_hash"] or tx["tx_hash"] in seen_tx_hashes:
                        continue
                    seen_tx_hashes.add(tx["tx_hash"])
                    process_tx(tx, price_usd)
            except Exception as e:
                print(f"Error fetching {chain.upper()} txs:", e)
        time.sleep(POLL_INTERVAL)
