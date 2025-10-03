import threading
import time
from flask import Flask, render_template, jsonify
from utils.price import price_cache
from watchtower import seen_tx_hashes, load_chain_handler
from config import CHAINS

app = Flask(__name__)

recent_txs = []


@app.route("/")
def index():
    return render_template("index.html", txs=recent_txs)


@app.route("/api/txs")
def get_txs():
    return jsonify(recent_txs)


@app.template_filter("explorer_url")
def explorer_url_filter(tx):
    chain = tx.get("chain", "").upper()
    tx_hash = tx.get("tx_hash", "")
    if chain == "BTC":
        return f"https://www.blockchain.com/btc/tx/{tx_hash}"
    return "#"


def update_recent_txs():
    chain_handlers = {name: load_chain_handler(name) for name in CHAINS}
    for chain, handler in chain_handlers.items():
        price_usd = price_cache.get_price(chain.upper())
        try:
            txs = handler.fetch_unconfirmed_txs()
            for tx_raw in txs:
                tx = handler.parse_tx(tx_raw)
                if not tx["tx_hash"] or tx["tx_hash"] in seen_tx_hashes:
                    continue
                seen_tx_hashes.add(tx["tx_hash"])
                value_usd = tx["value"] * price_usd
                tx["usd"] = value_usd
                recent_txs.insert(0, tx)
                if len(recent_txs) > 100:
                    recent_txs.pop()
        except Exception as e:
            print(f"Error fetching {chain.upper()} txs:", e)


def poller():
    while True:
        update_recent_txs()
        time.sleep(5)


threading.Thread(target=poller, daemon=True).start()
