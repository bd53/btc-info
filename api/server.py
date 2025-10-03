import threading
import time
from flask import Flask, render_template, jsonify
from utils.price import price_cache
from monitor import add_to_seen_hashes, load_chain_handler
from config import CHAINS

app = Flask(__name__)

MAX_RECENT_TXS = 100
recent_txs = []

@app.route("/")
def index():
    btc_price = price_cache.get_price("BTC")
    return render_template("index.html", txs=list(recent_txs), btc_price=btc_price)

@app.route("/api/txs")
def get_txs():
    return jsonify(list(recent_txs))

@app.route("/api/stats")
def get_stats():
    from monitor import stats, seen_tx_set

    return jsonify(
        {
            "total_txs": stats["total_txs"],
            "large_txs": stats["large_txs"],
            "errors": stats["errors"],
            "uptime": time.time() - stats["start_time"],
            "tracked_hashes": len(seen_tx_set),
            "by_chain": stats["by_chain"],
        }
    )

@app.template_filter("explorer_url")
def explorer_url_filter(tx):
    chain = tx.get("chain", "").upper()
    tx_hash = tx.get("hash", "")

    if chain == "BTC":
        return f"https://www.blockchain.com/btc/tx/{tx_hash}"
    elif chain == "ETH":
        return f"https://etherscan.io/tx/{tx_hash}"

    return "#"

def update_recent_txs():
    chain_handlers = {}
    for name in CHAINS:
        try:
            chain_handlers[name] = load_chain_handler(name)
        except Exception as e:
            print(f"Error loading {name} handler: {e}")

    for chain, handler in chain_handlers.items():
        price_usd = price_cache.get_price(chain.upper())

        if price_usd == 0:
            continue

        try:
            txs = handler.fetch_unconfirmed_txs()

            for tx_raw in txs:
                try:
                    tx = handler.parse_tx(tx_raw)

                    if not tx.get("hash"):
                        continue

                    if add_to_seen_hashes(tx["hash"]):
                        continue

                    value_usd = tx["value"] * price_usd
                    tx["usd"] = value_usd

                    recent_txs.insert(0, tx)

                    if len(recent_txs) > MAX_RECENT_TXS:
                        recent_txs.pop()

                except Exception as e:
                    print(f"Error parsing {chain.upper()} transaction: {e}")

        except Exception as e:
            print(f"Error fetching {chain.upper()} txs: {e}")

def poller():
    print("Starting API transaction poller...")

    while True:
        try:
            update_recent_txs()
        except Exception as e:
            print(f"Error in poller: {e}")

        time.sleep(5)

poller_thread = threading.Thread(target=poller, daemon=True)
poller_thread.start()
