import threading
import webbrowser
import time
import sys
from api.server import app
from monitor import poll_loop, print_statistics
from config import DEV_ENV

def open_browser():
    time.sleep(2)
    try:
        print(f"Opening browser at {DEV_ENV}")
        webbrowser.open(DEV_ENV)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Please open {DEV_ENV} manually")

def run_console_monitor():
    try:
        poll_loop()
    except KeyboardInterrupt:
        print("\n\nShutting down console monitor...")
        print_statistics()
    except Exception as e:
        print(f"\n✗ Fatal error in console monitor: {e}")
        print_statistics()
        raise

def run_web_server():
    try:
        print("Starting web server...")
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
    except Exception as e:
        print(f"\nFatal error in web server: {e}")
        raise

def print_banner():
    print(f"{'─'*60}")
    print("                     ₿ BITCOIN MONITOR")
    print(f"{'─'*60}")
    print("Choose mode:")
    print("  1. Web Dashboard (Flask server + auto-open browser)")
    print("  2. Console Monitor (terminal output only)")
    print("  3. Both (Web Dashboard + Console Monitor)")
    print(f"{'─'*60}")

if __name__ == "__main__":
    print_banner()

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("Select mode (1/2/3) [default: 1]: ").strip() or "1"

    print()

    if mode == "1":
        print("Starting in web dashboard mode...")
        print("─" * 60)
        threading.Thread(target=open_browser, daemon=True).start()

        try:
            run_web_server()
        except KeyboardInterrupt:
            print("\n\nShutting down web server...")

    elif mode == "2":
        print("Starting in console monitor mode...")
        print("─" * 60)
        run_console_monitor()

    elif mode == "3":
        print("Starting in dual mode... (Web Dashboard + Console Monitor)")
        print("─" * 60)

        server_thread = threading.Thread(target=run_web_server, daemon=True)
        server_thread.start()

        threading.Thread(target=open_browser, daemon=True).start()

        try:
            run_console_monitor()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            print_statistics()

    else:
        print(f"Invalid mode: {mode}")
        print("Please choose 1, 2, or 3")
        sys.exit(1)
