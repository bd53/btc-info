import requests
from utils.format import satoshi_to_btc
from config import BTC_URL

def fetch_unconfirmed_txs():
    r = requests.get(BTC_URL, timeout=10)
    r.raise_for_status()
    return r.json().get("txs", [])

def parse_tx(tx):
    try:
        from_addr = tx["inputs"][0]["prev_out"].get("addr", "unknown")
    except (IndexError, KeyError):
        from_addr = "unknown"

    try:
        to_addr = tx["out"][0].get("addr", "unknown")
        value_btc = satoshi_to_btc(tx["out"][0].get("value", 0))
    except (IndexError, KeyError):
        to_addr = "unknown"
        value_btc = 0.0

    return {
        "chain": "BTC",
        "tx_hash": tx.get("hash"),
        "from": from_addr,
        "to": to_addr,
        "value": value_btc,
        "value_str": f"{value_btc:.8f} BTC",
        "status": "pending" or "confirmed",
    }
