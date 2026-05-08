"""
counter/app.py — Service Décompteur
PORT : 5004
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from crypto.rsa_core import generate_rsa_keypair
from crypto.rsa_ops import rsa_decrypt, rsa_verify
from crypto.encoding import tth, unpack_vote 

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["*"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

COMMISSIONER_URL  = os.environ.get("COMMISSIONER_URL",  "http://localhost:5001")
ADMINISTRATOR_URL = os.environ.get("ADMINISTRATOR_URL", "http://localhost:5002")

STATE = {
    "e": None, "d": None, "N": None,
    "ballot_box": [],   # { encrypted_ballot, signature, m_int, timestamp }
    "results": {},
    "phase": "setup",  # setup → ready → counting → done
    "audit": [],
}


def log(msg):
    STATE["audit"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    print(f"[COUNTER] {msg}")


def get_admin_pubkey():
    try:
        r = requests.get(f"{ADMINISTRATOR_URL}/api/public_key", timeout=5)
        d = r.json()
        return int(d["e"]), int(d["N"])   # ← add int() here
    except Exception as ex:
        log(f"Impossible de récupérer la clé admin : {ex}")
        return None, None


def verify_tth_at_commissioner(tth_n2: str) -> bool:
    try:
        r = requests.post(f"{COMMISSIONER_URL}/api/verify_tth_N2",
                          json={"tth_N2": tth_n2}, timeout=5)
        return r.json().get("valid", False)
    except Exception as ex:
        log(f"Erreur commissaire (verify_tth) : {ex}")
        return False


def get_candidates_from_commissioner():
    try:
        r = requests.get(f"{COMMISSIONER_URL}/api/state", timeout=5)
        return r.json().get("candidates", [])
    except Exception:
        return []


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"service": "counter", "status": "ok",
                    "keys_ready": STATE["e"] is not None,
                    "ballots": len(STATE["ballot_box"])})


# ── keys generation ────────────────────────────────────────────────────────
@app.route("/api/generate_keys", methods=["POST"])
def generate_keys():
    bits = request.json.get("bits", 2048) if request.json else 2048
    log(f"Generation des cles RSA {bits} bits...")
    e, d, N = generate_rsa_keypair(bits=bits)
    STATE["e"], STATE["d"], STATE["N"] = e, d, N
    STATE["phase"] = "ready"
    log("Cles generees avec succes")
    return jsonify({
    "ok": True,
    "public_key": {
        "e": str(e),
        "N": str(N)
    }
})


@app.route("/api/public_key")
def public_key():
    if STATE["e"] is None:
        return jsonify({"error": "Clés non générées"}), 503
    return jsonify({
    "e": str(STATE["e"]),
    "N": str(STATE["N"])
})


# ── Reception of ballot ────────────────────────
@app.route("/api/receive_ballot", methods=["POST"])
def receive_ballot():
    if STATE["d"] is None:
        return jsonify({"error": "Décompteur non initialisé"}), 503
    data = request.json
    try:
        encrypted_ballot = int(data.get("encrypted_ballot"))
        signature        = int(data.get("signature"))
        # m_int no longer stored — counter recomputes it from decrypted data
    except (TypeError, ValueError):
        return jsonify({"error": "Données invalides"}), 400

    STATE["ballot_box"].append({
        "encrypted_ballot": encrypted_ballot,
        "signature":        signature,
        "timestamp":        datetime.now().isoformat(),
    })
    log(f"Bulletin #{len(STATE['ballot_box'])} reçu")
    return jsonify({"ok": True, "ballot_count": len(STATE["ballot_box"])})

# ── Counting ──────────────────────────────────────────────────────────────

@app.route("/api/count_votes", methods=["POST"])
def count_votes():
    if STATE["phase"] not in ("ready", "counting"):
        return jsonify({"error": "Phase incorrecte"}), 400
    if STATE["d"] is None:
        return jsonify({"error": "Clés non générées"}), 503

    STATE["phase"] = "counting"
    candidates = get_candidates_from_commissioner()
    e_A, N_A = get_admin_pubkey()
    if e_A is None:
        return jsonify({"error": "Clé admin indisponible"}), 503

    results = {c: 0 for c in candidates}
    valid_count = 0
    invalid_count = 0
    ballot_details = []

    log(f"Début du dépouillement — {len(STATE['ballot_box'])} bulletins")

    for i, ballot in enumerate(STATE["ballot_box"]):
        enc   = ballot["encrypted_ballot"]
        sig   = ballot["signature"]
        num   = i + 1

        # ── Step 1: decrypt ballot → recover packed(choice | N2) ──────────────
        try:
            packed = rsa_decrypt(enc, STATE["d"], STATE["N"])
        except Exception as ex:
            log(f"Bulletin #{num} rejeté — déchiffrement : {ex}")
            invalid_count += 1
            ballot_details.append({"num": num, "status": "FAIL déchiffrement"})
            continue

        # ── Step 2: unpack → extract vote_index and N2 ────────────────────────
        try:
            vote_index, N2 = unpack_vote(packed)
            log(f"Bulletin #{num} — vote_index={vote_index}, N2={N2!r}") 
        except ValueError as ex:
            log(f"Bulletin #{num} rejeté — décodage : {ex}")
            invalid_count += 1
            ballot_details.append({"num": num, "status": "FAIL décodage vote|N2"})
            continue

        # ── Step 3: recompute m_int from (vote_index, N2) and verify signature
        #    This is the critical check — we recompute m_int ourselves so a 
        #    cheater cannot forge it. sig^e mod N_A must equal our recomputed m_int
        from crypto.encoding import encode_vote
        recomputed_m_int = encode_vote(vote_index, N2, rsa_modulus=N_A)
        if not rsa_verify(recomputed_m_int, sig, e_A, N_A):
            log(f"Bulletin #{num} rejeté — signature admin invalide")
            invalid_count += 1
            ballot_details.append({"num": num, "status": "FAIL signature invalide"})
            continue

        # ── Step 4: hash N2 and verify it was registered with the commissioner ─
        computed_tth = tth(N2)
        log(f"Bulletin #{num} — computed_tth={computed_tth}")  
        if not verify_tth_at_commissioner(computed_tth):
            log(f"Bulletin #{num} rejeté — tth(N2) non reconnu")
            invalid_count += 1
            ballot_details.append({"num": num, "status": "FAIL N2 non enregistré"})
            continue

        # ── Step 5: validate vote index range ─────────────────────────────────
        if not candidates or vote_index < 0 or vote_index >= len(candidates):
            log(f"Bulletin #{num} rejeté — vote_index={vote_index} hors plage")
            invalid_count += 1
            ballot_details.append({"num": num, "status": f"FAIL index hors plage ({vote_index})"})
            continue

        # ── All checks passed ─────────────────────────────────────────────────
        candidate = candidates[vote_index]
        results[candidate] = results.get(candidate, 0) + 1
        valid_count += 1
        log(f"Bulletin #{num} valide → {candidate}")
        ballot_details.append({"num": num, "status": f"✓ Valide → {candidate}", "vote": candidate})

    STATE["results"] = results
    STATE["phase"] = "done"
    log(f"Dépouillement terminé — {valid_count} valides / {invalid_count} invalides")

    return jsonify({
        "ok": True,
        "results": results,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total": len(STATE["ballot_box"]),
        "ballot_details": ballot_details,
    })

# ── state ───────────────────────────────────────────────────────────────
@app.route("/api/state")
def get_state():
    return jsonify({
        "phase": STATE["phase"],
        "keys_ready": STATE["e"] is not None,
        "ballot_count": len(STATE["ballot_box"]),
        "results": STATE["results"],
        "audit": STATE["audit"][-30:],
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    STATE.update({
        "e": None, "d": None, "N": None,
        "ballot_box": [], "results": {}, "phase": "setup", "audit": [],
    })
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False ,threaded=True)
