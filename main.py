import threading
import webbrowser
import time
from api.server import app
from config import DEV_ENV


def open_browser():
    time.sleep(1)
    webbrowser.open(DEV_ENV)


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
