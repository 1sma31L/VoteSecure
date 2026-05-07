"""
server.py — Single-entry deployment for Render
All 5 services run in separate processes (gunicorn workers),
the website gateway listens on Render's $PORT.
"""
import os
import sys
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

PORT = int(os.environ.get("PORT", 5000))

# Set inter-service URLs BEFORE importing or launching
os.environ.setdefault("COMMISSIONER_URL",  "http://localhost:5001")
os.environ.setdefault("ADMINISTRATOR_URL", "http://localhost:5002")
os.environ.setdefault("ANONYMISER_URL",    "http://localhost:5003")
os.environ.setdefault("COUNTER_URL",      "http://localhost:5004")

# Launch each internal service as its own gunicorn process
# (separate GILs so RSA key generation doesn't block other services)
procs = []
for name, module, port in [
    ("commissioner",  "entities.commissioner.app:app",   5001),
    ("administrator", "entities.administrator.app:app",  5002),
    ("anonymiser",    "entities.anonymiser.app:app",     5003),
    ("counter",       "entities.counter.app:app",        5004),
]:
    p = subprocess.Popen(
        [
            sys.executable, "-m", "gunicorn",
            "--bind", f"0.0.0.0:{port}",
            "--workers", "1",
            "--timeout", "300",
            "--access-logfile", "-",
            module,
        ],
        cwd=BASE,
        env=os.environ.copy(),
    )
    procs.append(p)
    print(f"[server] {name} → :{port} (PID {p.pid})")

# Give internal services time to bind
time.sleep(3)

# Launch the website gateway with gunicorn on Render's PORT
print(f"[server] website → :{PORT}")
try:
    subprocess.run(
        [
            sys.executable, "-m", "gunicorn",
            "--bind", f"0.0.0.0:{PORT}",
            "--workers", "1",
            "--timeout", "300",
            "--access-logfile", "-",
            "website.app:app",
        ],
        cwd=BASE,
        env=os.environ.copy(),
    )
finally:
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
