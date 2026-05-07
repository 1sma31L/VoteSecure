#!/usr/bin/env python3

import subprocess, sys, os, time, signal, atexit

BASE = os.path.dirname(os.path.abspath(__file__))

SERVICES = [
    {
        "name": "Commissaire",
        "module": "entities.commissioner.app",
        "port": 5001,
        "env": {},
    },
    {
        "name": "Administrateur",
        "module": "entities.administrator.app",
        "port": 5002,
        "env": {
            "COMMISSIONER_URL": "http://localhost:5001",
        },
    },
    {
        "name": "Anonymiseur",
        "module": "entities.anonymiser.app",
        "port": 5003,
        "env": {
            "COMMISSIONER_URL":  "http://localhost:5001",
            "ADMINISTRATOR_URL": "http://localhost:5002",
            "COUNTER_URL":       "http://localhost:5004",
        },
    },
    {
        "name": "Décompteur",
        "module": "entities.counter.app",
        "port": 5004,
        "env": {
            "COMMISSIONER_URL":  "http://localhost:5001",
            "ADMINISTRATOR_URL": "http://localhost:5002",
        },
    },
    {
        "name": "Site Web",
        "module": "website.app",
        "port": 5000,
        "env": {
            "COMMISSIONER_URL":  "http://localhost:5001",
            "ADMINISTRATOR_URL": "http://localhost:5002",
            "ANONYMISER_URL":    "http://localhost:5003",
            "COUNTER_URL":       "http://localhost:5004",
        },
    },
]

procs = []


def cleanup():
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    for p in procs:
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
    print("[launcher] done.")


atexit.register(cleanup)


def main():
    print("=" * 60)
    print("=" * 60)

    env_base = os.environ.copy()
    env_base["PYTHONPATH"] = BASE

    for svc in SERVICES:
        env = {**env_base, **svc["env"]}
        cmd = [sys.executable, "-m", svc["module"]]
        p = subprocess.Popen(
            cmd,
            cwd=BASE,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        procs.append(p)
        print(f"  OK {svc['name']:20s} -> http://localhost:{svc['port']}  (PID {p.pid})")
        time.sleep(0.4)   # petit delai pour laisser le port s'ouvrir

    print()
    print("  Site Web -> http://localhost:5000")
    print()
    print("  Ctrl+C pour tout arrêter")
    print("=" * 60)

    # Forward
    import threading

    def stream(name, proc):
        for line in proc.stdout:
            print(f"[{name}] {line.decode(errors='replace').rstrip()}")

    for i, p in enumerate(procs):
        t = threading.Thread(target=stream, args=(SERVICES[i]["name"], p), daemon=True)
        t.start()

    
    try:
        while True:
            time.sleep(1)
           
            for i, p in enumerate(procs):
                if p.poll() is not None:
                    print(f"\n[launcher] ATTENTION : {SERVICES[i]['name']} s'est arrêté (code {p.returncode})")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
