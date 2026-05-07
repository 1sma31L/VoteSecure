"""
administrator/app.py — Service Administrateur
PORT : 5002
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from crypto.rsa_core import generate_rsa_keypair
from crypto.blind_signature import sign_blind

app = Flask(__name__)
CORS(app)


COMMISSIONER_URL = os.environ.get("COMMISSIONER_URL", "http://localhost:5001")

STATE = {
    "e": None, "d": None, "N": None,
    "used_N1": set(),           
    "audit": [],
}


def log(msg):
    STATE["audit"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    print(f"[ADMINISTRATOR] {msg}")


def ask_commissioner_validate(N1: str) -> bool:
    try:
        r = requests.post(f"{COMMISSIONER_URL}/api/validate_N1", json={"N1": N1}, timeout=5)
        return r.json().get("valid", False)
    except Exception as ex:
        log(f"Erreur commissaire : {ex}")
        return False


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"service": "administrator", "status": "ok",
                    "keys_ready": STATE["e"] is not None})


# ── keys generation ────────────────────────────────────────────────────────
@app.route("/api/generate_keys", methods=["POST"])
def generate_keys():
    bits = request.json.get("bits", 2048) if request.json else 2048
    log(f"Generation des cles RSA {bits} bits...")
    e, d, N = generate_rsa_keypair(bits=bits)
    STATE["e"], STATE["d"], STATE["N"] = e, d, N
    log("Cles generees avec succes")
    return jsonify({
    "ok": True,
    "public_key": {
        "e": str(e),
        "N": str(N)
    }
})


# ── public key  ──────────────────────────────────────────────────────────────
@app.route("/api/public_key")
def public_key():
    if STATE["e"] is None:
        return jsonify({"error": "Clés non générées"}), 503
    return jsonify({
        "e": str(STATE["e"]),
        "N": str(STATE["N"])
    })




# ── blind signing ─────────────────────────────────────────────────────────
@app.route("/api/sign_blind", methods=["POST"])
def sign_blind_route():
    if STATE["d"] is None:
        return jsonify({"error": "Clés non générées"}), 503

    data = request.json
    N1 = data.get("N1", "").replace(" ", "").upper()
    try:
        m_masked = int(data.get("m_masked"))
    except (TypeError, ValueError):
        return jsonify({"error": "m_masked invalide"}), 400

    if not (0 < m_masked < STATE["N"]):
        return jsonify({"error": "m_masked hors domaine"}), 400

   
    if N1 in STATE["used_N1"]:
        log(f"Refus N1={N1[:4]}... - deja utilise localement")
        return jsonify({"error": "N1 deja utilise"}), 403

    if not ask_commissioner_validate(N1):
        log(f"Refus N1={N1[:4]}... - commissaire rejette")
        return jsonify({"error": "N1 invalide selon le commissaire"}), 403

    STATE["used_N1"].add(N1)
    s_blind = sign_blind(m_masked, STATE["d"], STATE["N"])
    log(f"Signature aveugle émise pour N1={N1[:4]}…")
    return jsonify({"s_blind": str(s_blind)})


# ── state ──────────────────────────────────────────────────────────────
@app.route("/api/state")
def get_state():
    return jsonify({
        "keys_ready": STATE["e"] is not None,
        "signatures_issued": len(STATE["used_N1"]),
        "audit": STATE["audit"][-30:],
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    STATE.update({"e": None, "d": None, "N": None, "used_N1": set(), "audit": []})
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False , threaded=True)
