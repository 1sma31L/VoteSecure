"""
server.py — Single-entry deployment for Render
All 5 services run in separate processes.
Uses Flask dev server on Windows, gunicorn on Linux/production.
"""
import os
import sys
import subprocess
import time
import platform

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

PORT = int(os.environ.get("PORT", 5000))
IS_WINDOWS = platform.system() == "Windows"

# Set inter-service URLs BEFORE importing or launching
os.environ.setdefault("COMMISSIONER_URL",  "http://localhost:5001")
os.environ.setdefault("ADMINISTRATOR_URL", "http://localhost:5002")
os.environ.setdefault("ANONYMISER_URL",    "http://localhost:5003")
os.environ.setdefault("COUNTER_URL",      "http://localhost:5004")

procs = []

# Launch each internal service
for name, module, port in [
    ("commissioner",  "entities.commissioner.app:app",   5001),
    ("administrator", "entities.administrator.app:app",  5002),
    ("anonymiser",    "entities.anonymiser.app:app",     5003),
    ("counter",       "entities.counter.app:app",        5004),
]:
    if IS_WINDOWS:
        # Windows: use Python subprocess to run Flask directly
        module_name, app_var = module.split(":")
        p = subprocess.Popen(
            [
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, r'{BASE}'); "
                f"from {module_name} import {app_var} as app; "
                f"app.run(host='0.0.0.0', port={port}, debug=False, threaded=True, use_reloader=False)"
            ],
            cwd=BASE,
            env=os.environ.copy(),
        )
    else:
        # Linux/Production: use gunicorn
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

# Launch the website gateway
print(f"[server] website → :{PORT}")
try:
    if IS_WINDOWS:
        # Windows: use Flask dev server
        from website.app import app
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True, use_reloader=False)
    else:
        # Linux/Production: use gunicorn
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
