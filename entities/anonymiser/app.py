"""
anonymiser/app.py — Service Anonymiseur
PORT : 5003
"""

import os
import sys
from datetime import datetime
import secrets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from crypto.rsa_ops import rsa_verify

# ═══════════════════════════════════════════════════════════════════════════════
# Flask
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["*"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# URLs des services
# ═══════════════════════════════════════════════════════════════════════════════

COMMISSIONER_URL = os.environ.get(
    "COMMISSIONER_URL",
    "http://localhost:5001"
)

COUNTER_URL = os.environ.get(
    "COUNTER_URL",
    "http://localhost:5004"
)

ADMINISTRATOR_URL = os.environ.get(
    "ADMINISTRATOR_URL",
    "http://localhost:5002"
)

# ═══════════════════════════════════════════════════════════════════════════════
# État mémoire
# ═══════════════════════════════════════════════════════════════════════════════

STATE = {

    # Anti replay
    "seen_signatures": set(),

    # Bulletins stockés anonymement
    "stored_ballots": [],

    # Compteurs
    "accepted_count": 0,
    "rejected_count": 0,
    "forwarded_count": 0,

    # Reçus
    "receipts": {},

    # Logs
    "audit": [],
    
    # Cache admin public key (performance optimization)
    "cached_admin_key": None,
}

# ═══════════════════════════════════════════════════════════════════════════════
# LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log(message):

    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "msg": message
    }

    STATE["audit"].append(entry)

    print(f"[ANONYMISER] {message}")

# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/health")
def health():

    return jsonify({
        "service": "anonymiser",
        "status": "ok"
    })

# ═══════════════════════════════════════════════════════════════════════════════
# SOUMISSION D'UN VOTE
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/submit_vote", methods=["POST"])
def submit_vote():

    data = request.json

    if not data:
        return jsonify({
            "error": "JSON manquant"
        }), 400

    # ──────────────────────────────────────────────────────────────────────────
    # Récupération des données
    # ──────────────────────────────────────────────────────────────────────────

    N1 = data.get("N1", "").replace(" ", "").upper()

    try:

        encrypted_ballot = int(data.get("encrypted_ballot"))
        signature        = int(data.get("signature"))
        m_int            = int(data.get("m_int"))

    except (TypeError, ValueError):

        return jsonify({
            "error": "Données invalides"
        }), 400

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Anti Replay
    # ──────────────────────────────────────────────────────────────────────────

    if signature in STATE["seen_signatures"]:

        STATE["rejected_count"] += 1

        log("Rejet : signature déjà utilisée")

        return jsonify({
            "error": "Vote déjà soumis"
        }), 403

    STATE["seen_signatures"].add(signature)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Récupérer la clé publique admin (avec cache)
    # ──────────────────────────────────────────────────────────────────────────

    if STATE["cached_admin_key"] is None:
        try:
            r = requests.get(
                f"{ADMINISTRATOR_URL}/api/public_key",
                timeout=5
            )
            admin_data = r.json()
            STATE["cached_admin_key"] = {
                "e": int(admin_data["e"]),
                "N": int(admin_data["N"])
            }
            log("Admin public key cached")
        except Exception as ex:
            log(f"Impossible de récupérer la clé admin : {ex}")
            return jsonify({
                "error": "Administrateur indisponible"
            }), 503
    
    e_A = STATE["cached_admin_key"]["e"]
    N_A = STATE["cached_admin_key"]["N"]

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Vérification signature RSA
    # ──────────────────────────────────────────────────────────────────────────

    signature_valid = rsa_verify(
        m_int % N_A,
        signature,
        e_A,
        N_A
    )

    if not signature_valid:

        STATE["rejected_count"] += 1

        log("Rejet : signature RSA invalide")

        return jsonify({
            "error": "Signature invalide"
        }), 403

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Consommer N1 auprès du commissaire
    # ──────────────────────────────────────────────────────────────────────────

    try:

        r = requests.post(
            f"{COMMISSIONER_URL}/api/consume_N1",
            json={
                "N1": N1
            },
            timeout=5
        )

        ok = r.json().get("ok", False)

    except Exception as ex:

        log(f"Erreur commissaire : {ex}")

        return jsonify({
            "error": "Commissaire indisponible"
        }), 503

    if not ok:

        STATE["rejected_count"] += 1

        log(f"Rejet : N1 invalide ou déjà utilisé ({N1[:4]}...)")

        return jsonify({
            "error": "N1 invalide ou déjà utilisé"
        }), 403

    # ──────────────────────────────────────────────────────────────────────────
    # 5. ANONYMISATION
    # IMPORTANT :
    #       ON NE STOCKE PAS LE N1
    # ──────────────────────────────────────────────────────────────────────────
    tth_N2 = data.get("tth_N2", "")

    anonymous_ballot = {
      "encrypted_ballot": encrypted_ballot,
      "signature": signature,
      "m_int": m_int,
      "tth_N2": tth_N2,      
      "stored_at": datetime.now().isoformat()
    }

    STATE["stored_ballots"].append(anonymous_ballot)

    STATE["accepted_count"] += 1

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Reçu
    # ──────────────────────────────────────────────────────────────────────────

    receipt_id = secrets.token_hex(8)

    STATE["receipts"][receipt_id] = {

        "timestamp": datetime.now().isoformat(),
        "status": "stored",
        "forwarded": False
    }

    log(
        f"Vote accepté et anonymisé "
        f"(total={STATE['accepted_count']})"
    )

    return jsonify({

        "ok": True,

        "message": "Vote accepté et stocké anonymement",

        "receipt_id": receipt_id,

        "stored_ballots": len(STATE["stored_ballots"])
    })

# ═══════════════════════════════════════════════════════════════════════════════
# ENVOI FINAL AU DÉCOMPTEUR
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/forward_all_ballots", methods=["POST"])
def forward_all_ballots():

    if len(STATE["stored_ballots"]) == 0:

        return jsonify({
            "error": "Aucun bulletin à envoyer"
        }), 400

    success_count = 0
    failed_count = 0

    # ──────────────────────────────────────────────────────────────────────────
    # Envoi un par un au décompteur
    # ──────────────────────────────────────────────────────────────────────────

    for ballot in STATE["stored_ballots"]:

        try:

            r = requests.post(

                f"{COUNTER_URL}/api/receive_ballot",

            json={
                "encrypted_ballot": ballot["encrypted_ballot"],
                "signature":        ballot["signature"],
                },

                timeout=10
            )

            ok = r.json().get("ok", False)

            if ok:

                success_count += 1

            else:

                failed_count += 1

        except Exception as ex:

            failed_count += 1

            log(f"Erreur envoi décompteur : {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # Mise à jour des stats
    # ──────────────────────────────────────────────────────────────────────────

    STATE["forwarded_count"] += success_count

    log(
        f"Transmission terminée : "
        f"{success_count} succès / "
        f"{failed_count} erreurs"
    )

    return jsonify({

        "ok": True,

        "forwarded": success_count,

        "failed": failed_count,

        "total_sent": STATE["forwarded_count"]
    })

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/state")
def get_state():

    return jsonify({

        "stored_ballots":
            len(STATE["stored_ballots"]),

        "accepted_count":
            STATE["accepted_count"],

        "rejected_count":
            STATE["rejected_count"],

        "forwarded_count":
            STATE["forwarded_count"],

        "audit":
            STATE["audit"][-30:]
    })

# ═══════════════════════════════════════════════════════════════════════════════
# RECEIPT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/receipt/<receipt_id>")
def get_receipt(receipt_id):

    receipt = STATE["receipts"].get(receipt_id)

    if not receipt:

        return jsonify({
            "error": "Reçu introuvable"
        }), 404

    return jsonify(receipt)

# ═══════════════════════════════════════════════════════════════════════════════
# RESET
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/reset", methods=["POST"])
def reset():

    STATE.update({

        "seen_signatures": set(),

        "stored_ballots": [],

        "accepted_count": 0,

        "rejected_count": 0,

        "forwarded_count": 0,

        "receipts": {},

        "audit": [],
        
        "cached_admin_key": None,
    })

    log("Reset complet")

    return jsonify({
        "ok": True
    })

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5003,
        debug=False,
        threaded=True
    )