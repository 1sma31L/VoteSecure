"""
server.py — Single-entry deployment for Render
All 5 services run in one process on internal ports,
the website gateway listens on Render's $PORT.
"""
import os
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

PORT = int(os.environ.get("PORT", 5000))

# Set inter-service URLs BEFORE importing the apps
# so they read the correct values from os.environ
os.environ.setdefault("COMMISSIONER_URL",  "http://localhost:5001")
os.environ.setdefault("ADMINISTRATOR_URL", "http://localhost:5002")
os.environ.setdefault("ANONYMISER_URL",    "http://localhost:5003")
os.environ.setdefault("COUNTER_URL",      "http://localhost:5004")

# Import all Flask apps (they pick up the env vars above)
from entities.commissioner.app  import app as comm_app
from entities.administrator.app import app as admin_app
from entities.anonymiser.app    import app as anon_app
from entities.counter.app       import app as counter_app
from website.app                import app as web_app


def run_app(app, port):
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


# Start internal services in daemon threads
for name, app_obj, port in [
    ("commissioner",  comm_app,   5001),
    ("administrator", admin_app,  5002),
    ("anonymiser",    anon_app,   5003),
    ("counter",       counter_app,5004),
]:
    threading.Thread(target=run_app, args=(app_obj, port), daemon=True).start()
    print(f"[server] {name} → :{port}")

# Give internal services a moment to bind
import time; time.sleep(1)

# Main thread runs the website gateway on Render's PORT
print(f"[server] website → :{PORT}")
web_app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
