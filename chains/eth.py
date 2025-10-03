import requests
from config import ETH_URL

def fetch_unconfirmed_txs():
    r = requests.get(ETH_URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data

def parse_tx(tx):
    try:
        from_addr = tx["inputs"][0]["addresses"][0]
    except (IndexError, KeyError):
        from_addr = "unknown"

    try:
        to_addr = tx["outputs"][0]["addresses"][0]
    except (IndexError, KeyError):
        to_addr = "unknown"

    try:
        value_wei = tx["outputs"][0].get("value", 0)
        value_eth = value_wei / 1e18
    except (KeyError, TypeError):
        value_eth = 0.0

    status = "confirmed" if tx.get("confirmations", 0) > 0 else "pending"

    return {
        "chain": "ETH",
        "tx_hash": tx.get("hash"),
        "from": from_addr,
        "to": to_addr,
        "value": value_eth,
        "value_str": f"{value_eth:.8f} ETH",
        "status": status,
    }