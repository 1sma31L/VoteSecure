"""
website/app.py — Site Web (Interface Électeur + Admin)
PORT : 5000
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


COMMISSIONER_URL = os.environ.get("COMMISSIONER_URL", "http://localhost:5001")
ADMINISTRATOR_URL = os.environ.get("ADMINISTRATOR_URL", "http://localhost:5002")
ANONYMISER_URL = os.environ.get("ANONYMISER_URL", "http://localhost:5003")
COUNTER_URL = os.environ.get("COUNTER_URL", "http://localhost:5004")


def proxy_get(url, timeout=30):
    try:
        r = requests.get(url, timeout=timeout)
        return jsonify(r.json()), r.status_code
    except Exception as ex:
        return jsonify({"error": str(ex)}), 503


def proxy_post(url, data=None, timeout=120, retries=1):

    payload = data or request.json
    last_ex = None

    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            return jsonify(r.json()), r.status_code
        except requests.exceptions.Timeout as ex:
            last_ex = ex
            if attempt < retries:
                time.sleep(1)
            continue
        except Exception as ex:
            return jsonify({"error": str(ex)}), 503

    return jsonify({"error": f"Timeout after {retries + 1} attempt(s): {last_ex}"}), 503


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"service": "website", "status": "ok"})


# ── main page ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── services ────────────────────────────────────────────────────
@app.route("/api/services")
def services():
    """Retourne les URLs et états de santé de tous les services."""
    results = {}
    for name, url in [
        ("commissioner", COMMISSIONER_URL),
        ("administrator", ADMINISTRATOR_URL),
        ("anonymiser", ANONYMISER_URL),
        ("counter", COUNTER_URL),
    ]:
        try:
            r = requests.get(f"{url}/health", timeout=3)
            results[name] = {"url": url, **r.json()}
        except Exception:
            results[name] = {"url": url, "status": "offline"}
    return jsonify(results)


# ── Crypto public keys ─────────────────────────────────────────────────
@app.route("/api/crypto_params")
def crypto_params():
    params = {}

    try:
        r = requests.get(f"{ADMINISTRATOR_URL}/api/public_key", timeout=5)
        data = r.json()
        params["admin"] = {
            "e": str(data["e"]),
            "N": str(data["N"]),
        }
    except Exception:
        params["admin"] = None

    try:
        r = requests.get(f"{COUNTER_URL}/api/public_key", timeout=5)
        data = r.json()
        params["counter"] = {
            "e": str(data["e"]),
            "N": str(data["N"]),
        }
    except Exception:
        params["counter"] = None

    return jsonify(params)


# ─────Commissioner────────────────────────────────────────────────────
@app.route("/api/commissioner/state")
def commissioner_state():
    return proxy_get(f"{COMMISSIONER_URL}/api/state")


@app.route("/api/commissioner/setup", methods=["POST"])
def commissioner_setup():
    return proxy_post(f"{COMMISSIONER_URL}/api/setup")


@app.route("/api/commissioner/register_voter", methods=["POST"])
def commissioner_register():
    return proxy_post(f"{COMMISSIONER_URL}/api/register_voter")


@app.route("/api/commissioner/open_voting", methods=["POST"])
def commissioner_open():
    return proxy_post(f"{COMMISSIONER_URL}/api/open_voting")


@app.route("/api/commissioner/close_voting", methods=["POST"])
def commissioner_close():
    result = proxy_post(f"{COMMISSIONER_URL}/api/close_voting")

    try:
        requests.post(f"{ANONYMISER_URL}/api/forward_all_ballots", timeout=30)
    except Exception:
        pass
    return result


@app.route("/api/commissioner/validate_N1_check", methods=["POST"])
def commissioner_validate_n1():
    return proxy_post(f"{COMMISSIONER_URL}/api/validate_N1")


# ── Admin────────────────────────────────────────────────────
@app.route("/api/administrator/state")
def admin_state():
    return proxy_get(f"{ADMINISTRATOR_URL}/api/state")


@app.route("/api/administrator/generate_keys", methods=["POST"])
def admin_gen_keys():
    return proxy_post(f"{ADMINISTRATOR_URL}/api/generate_keys", timeout=60, retries=1)


@app.route("/api/administrator/sign_blind", methods=["POST"])
def admin_sign():
    return proxy_post(f"{ADMINISTRATOR_URL}/api/sign_blind")


# ── counter ────────────────────────────────────────────────────────
@app.route("/api/counter/state")
def counter_state():
    return proxy_get(f"{COUNTER_URL}/api/state")


@app.route("/api/counter/generate_keys", methods=["POST"])
def counter_gen_keys():
    return proxy_post(f"{COUNTER_URL}/api/generate_keys", timeout=60, retries=1)


@app.route("/api/counter/count_votes", methods=["POST"])
def counter_count():
    return proxy_post(f"{COUNTER_URL}/api/count_votes", timeout=30)


# ── forward ballots ────────────────────────────────────────────
@app.route("/api/forward_all_ballots", methods=["POST"])
def forward_all_ballots():
    return proxy_post(f"{ANONYMISER_URL}/api/forward_all_ballots", timeout=30)


# ── Proxy vote ─────────────────────────────────────────────
@app.route("/api/vote/submit", methods=["POST"])
def vote_submit():
    return proxy_post(f"{ANONYMISER_URL}/api/submit_vote")


# ── Reset global ──────────────────────────────────────────────────────────────
@app.route("/api/reset_all", methods=["POST"])
def reset_all():
    results = {}
    for name, url in [
        ("commissioner", COMMISSIONER_URL),
        ("administrator", ADMINISTRATOR_URL),
        ("anonymiser", ANONYMISER_URL),
        ("counter", COUNTER_URL),
    ]:
        try:
            r = requests.post(f"{url}/api/reset", timeout=5)
            results[name] = r.json()
        except Exception as ex:
            results[name] = {"error": str(ex)}
    return jsonify({"ok": True, "results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)