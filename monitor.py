import importlib
import time
from collections import deque
from datetime import datetime
from typing import Dict, Set, Any
from utils.price import price_cache
from config import POLL_INTERVAL, LARGE_TX_THRESHOLD_USD, CHAINS

MAX_SEEN_HASHES = 10000
seen_tx_hashes: deque = deque(maxlen=MAX_SEEN_HASHES)
seen_tx_set: Set[str] = set()

stats = {
    "total_txs": 0,
    "large_txs": 0,
    "errors": 0,
    "start_time": time.time(),
    "by_chain": {},
}

def load_chain_handler(name: str):
    try:
        module = importlib.import_module(f"chains.{name}")
        if not hasattr(module, "fetch_unconfirmed_txs"):
            raise AttributeError(f"Module chains.{name} missing fetch_unconfirmed_txs()")
        if not hasattr(module, "parse_tx"):
            raise AttributeError(f"Module chains.{name} missing parse_tx()")
        return module
    except ImportError as e:
        print(f"✗ Failed to load chain handler for {name}: {e}")
        raise
    except AttributeError as e:
        print(f"✗ Invalid chain handler for {name}: {e}")
        raise

def add_to_seen_hashes(tx_hash: str):
    if tx_hash in seen_tx_set:
        return True

    seen_tx_hashes.append(tx_hash)
    seen_tx_set.add(tx_hash)

    if len(seen_tx_set) > MAX_SEEN_HASHES * 1.5:
        seen_tx_set.clear()
        seen_tx_set.update(seen_tx_hashes)

    return False

def format_value_with_color(value_usd: float, threshold: float) -> str:
    if value_usd > threshold:
        return f"${value_usd:,.2f} USD"
    elif value_usd > threshold * 0.5:
        return f"${value_usd:,.2f} USD"
    else:
        return f"${value_usd:,.2f} USD"

def process_tx(tx: Dict[str, Any], price_usd: float):
    value_usd = tx["value"] * price_usd
    is_large = value_usd > LARGE_TX_THRESHOLD_USD

    stats["total_txs"] += 1
    chain = tx["chain"]
    if chain not in stats["by_chain"]:
        stats["by_chain"][chain] = {"count": 0, "total_value": 0}
    stats["by_chain"][chain]["count"] += 1
    stats["by_chain"][chain]["total_value"] += value_usd

    if is_large:
        stats["large_txs"] += 1

    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"{'─'*60}")
    title = f"[{timestamp}] [{tx['chain']}] New Transaction"
    if is_large:
        title += " 🚩"
    print(title)
    print(f"{'─'*60}")
    print(f"Hash: {tx['tx_hash']}")
    print(f"From: {tx['from']}")
    print(f"To: {tx['to']}")
    print(f"Value: {tx['value_str']}")
    print(f"USD: {format_value_with_color(value_usd, LARGE_TX_THRESHOLD_USD)}")
    print(f"Status: {tx['status']}")
    print(f"{'─'*60}")

def print_statistics():
    uptime = time.time() - stats["start_time"]
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    print(f"\n{'─'*60}")
    print("                     ₿ BITCOIN MONITOR")
    print(f"{'─'*60}")
    print(f"Uptime: {hours}h {minutes}m")
    print(f"Total Transactions: {stats['total_txs']}")
    print(f"Large Transactions: {stats['large_txs']}")
    print(f"Errors: {stats['errors']}")
    print(f"Tracked Hashes: {len(seen_tx_set)}/{MAX_SEEN_HASHES}")

    if stats["by_chain"]:
        print(f"\nBy Chain:")
        for chain, data in stats["by_chain"].items():
            avg_value = data["total_value"] / data["count"] if data["count"] > 0 else 0
            print(f"  {chain}: {data['count']} txs, avg ${avg_value:,.2f}")

    print(f"{'─'*60}\n")

def poll_chain(chain: str, handler, price_usd: float) -> int:
    new_tx_count = 0

    try:
        txs = handler.fetch_unconfirmed_txs()

        if not txs:
            return 0

        for tx_raw in txs:
            try:
                tx = handler.parse_tx(tx_raw)

                if not tx.get("tx_hash"):
                    continue

                if add_to_seen_hashes(tx["tx_hash"]):
                    continue

                process_tx(tx, price_usd)
                new_tx_count += 1

            except Exception as e:
                print(f"✗ Error parsing {chain.upper()} transaction: {e}")
                stats["errors"] += 1

    except Exception as e:
        print(f"✗ Error fetching {chain.upper()} transactions: {e}")
        stats["errors"] += 1

    return new_tx_count

def poll_loop():
    print(f"\n{'='*60}")
    print(f"Starting monitor...")
    print(f"{'='*60}")
    print(f"Monitoring chains: {', '.join(CHAINS)}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"Large tx threshold: ${LARGE_TX_THRESHOLD_USD:,}")
    print(f"{'='*60}\n")

    chain_handlers: Dict[str, Any] = {}
    for name in CHAINS:
        try:
            chain_handlers[name] = load_chain_handler(name)
            print(f"✓ Loaded handler for {name.upper()}")
        except Exception as e:
            print(f"✗ Failed to load {name.upper()}, skipping: {e}")

    if not chain_handlers:
        print("✗ No valid chain handlers loaded. Exiting.")
        return

    print(f"\n{'─'*60}\n")

    poll_count = 0
    stats_interval = 20

    while True:
        poll_count += 1
        cycle_start = time.time()

        for chain, handler in chain_handlers.items():
            price_usd = price_cache.get_price(chain.upper())

            if price_usd == 0:
                print(f"Skipping {chain.upper()} poll - price unavailable")
                continue

            new_txs = poll_chain(chain, handler, price_usd)

            if new_txs > 0:
                print(f"✓ Found {new_txs} new {chain.upper()} transaction(s)")

        if poll_count % stats_interval == 0:
            print_statistics()

        cycle_duration = time.time() - cycle_start
        sleep_time = max(0, POLL_INTERVAL - cycle_duration)

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f" Warning: Poll cycle took {cycle_duration:.2f}s (longer than {POLL_INTERVAL}s interval)")