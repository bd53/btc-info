import datetime
import requests
from utils.format import satoshi_to_btc
from config import BTC_URL
from utils.price import price_cache

def fetch_unconfirmed_txs():
    r = requests.get(BTC_URL, timeout=10)
    r.raise_for_status()
    return r.json().get("txs", [])

def parse_tx(tx):
    try:
        sender_addr = tx["inputs"][0]["prev_out"].get("addr", "unknown")
    except (IndexError, KeyError):
        sender_addr = "unknown"

    try:
        receiver_addr = tx["out"][0].get("addr", "unknown")
        value_sats = tx["out"][0].get("value", 0)
        value_btc = satoshi_to_btc(value_sats)
    except (IndexError, KeyError):
        receiver_addr = "unknown"
        value_btc = 0.0
        value_sats = 0

    fee_sats = tx.get("fee", 0)
    fee_btc = satoshi_to_btc(fee_sats)
    fee_str = f"{fee_btc:.8f} BTC"

    btc_price = price_cache.get_price("BTC")
    value_usd = value_btc * btc_price
    fee_usd = fee_btc * btc_price

    confirmations = tx.get("confirmations", 0)
    status = "confirmed" if confirmations > 0 else "pending"

    return {
        "chain": "BTC",
        "hash": tx.get("hash"),
        "sender": sender_addr,
        "receiver": receiver_addr,
        "value": value_btc,
        "value_str": f"{value_btc:.8f} BTC",
        "value_usd": value_usd,
        "status": status,
        "confirmations": confirmations,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "fee": fee_btc,
        "fee_str": fee_str,
        "fee_usd": fee_usd,
    }
