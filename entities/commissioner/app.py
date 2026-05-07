"""
commissioner/app.py — Service Commissaire
Responsabilités :
  - Inscrire les électeurs (génère N1, N2, tth(N2))
  - Valider / consommer les N1 lors du vote
  - Vérifier les tth(N2) lors du dépouillement
  - Ouvrir / fermer le scrutin
PORT : 5001
"""
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crypto.encoding import generate_code, format_code, tth

app = Flask(__name__)
CORS(app)

# ── Config email ───────────────────────────────────────────────────────────────
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER",   "voteadmin2005@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "gaab vfyt razk urzz")
EMAIL_SMTP     = "smtp.gmail.com"
EMAIL_PORT     = 587

STATE = {
    "phase": "setup",
    "election_title": "",
    "candidates": [],
    "voters": {},               # voter_id → { name, email, N1, N2, tth_N2, voted }
    "valid_N1": set(),          # N1 codes still usable
    "used_N1": set(),           # N1 codes already consumed
    "tth_N2_set": set(),        # all registered tth(N2)
    "audit": [],
}


def log(msg):
    STATE["audit"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    print(f"[COMMISSIONER] {msg}")

def send_voter_credentials(to_email: str, voter_name: str, n1_fmt: str, n2_fmt: str, title: str):
    """Send N1 and N2 codes to the voter by email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your voting codes {title}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = to_email

    body = f"""Hello {voter_name},

You are registered for the election: {title}

Here are your personal and confidential codes:

  N1 Code (identification): {n1_fmt}
  N2 Code (anonymity):      {n2_fmt}

IMPORTANT:
  - Do not share these codes with anyone.
  - The N1 code will be required to access the voting system.
  - The N2 code ensures the anonymity of your ballot.

---
Secure electronic voting system
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as ex:
        log(f"Failed to send email to {to_email}: {ex}")
        return False

# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"service": "commissioner", "status": "ok", "phase": STATE["phase"]})


# ── Setup ──────────────────────────────────────────────────────────────────────
@app.route("/api/setup", methods=["POST"])
def setup():
    data = request.json
    title = data.get("title", "Élection")
    candidates = [c.strip() for c in data.get("candidates", []) if c.strip()]
    if len(candidates) < 2:
        return jsonify({"error": "Au moins 2 candidats requis"}), 400
    STATE["election_title"] = title
    STATE["candidates"] = candidates
    STATE["phase"] = "registration"
    log(f"Élection '{title}' configurée — candidats : {candidates}")
    return jsonify({"ok": True, "phase": "registration"})


# ── Inscription ────────────────────────────────────────────────────────────────
@app.route("/api/register_voter", methods=["POST"])
def register_voter():
    if STATE["phase"] != "registration":
        return jsonify({"error": "Pas en phase d'inscription"}), 400

    name  = request.json.get("name", "Électeur")
    email = request.json.get("email", "").strip()

    voter_id = secrets.token_hex(8)
    N1 = generate_code(12)
    N2 = generate_code(12)
    tth_n2 = tth(N2)

    STATE["valid_N1"].add(N1)
    STATE["tth_N2_set"].add(tth_n2)
    STATE["voters"][voter_id] = {
        "name": name, "email": email,
        "N1": N1, "N2": N2, "tth_N2": tth_n2, "voted": False
    }

    n1_fmt = format_code(N1)
    n2_fmt = format_code(N2)

    # Send credentials by email
    email_sent = False
    if email:
        email_sent = send_voter_credentials(
            email, name, n1_fmt, n2_fmt, STATE["election_title"]
        )
        log(f"Electeur '{name}' <{email}> — email {'envoye' if email_sent else 'ECHEC'}")
    else:
        log(f"Electeur '{name}' inscrit sans email (N1={N1[:4]}...)")

    return jsonify({
        "ok": True,
        "voter_id": voter_id,
        "N1": N1, "N2": N2,
        "N1_formatted": n1_fmt,
        "N2_formatted": n2_fmt,
        "tth_N2": tth_n2,
        "email_sent": email_sent,
    })


@app.route("/api/open_voting", methods=["POST"])
def open_voting():
    if STATE["phase"] != "registration":
        return jsonify({"error": "Pas en phase d'inscription"}), 400
    if not STATE["voters"]:
        return jsonify({"error": "Aucun électeur inscrit"}), 400
    STATE["phase"] = "voting"
    log(f"Scrutin ouvert — {len(STATE['voters'])} électeurs inscrits")
    return jsonify({"ok": True, "phase": "voting"})


@app.route("/api/close_voting", methods=["POST"])
def close_voting():
    STATE["phase"] = "counting"
    log("Scrutin clos")
    return jsonify({"ok": True, "phase": "counting"})


# ── Validation of N1 ────────────────────────────────
@app.route("/api/validate_N1", methods=["POST"])
def validate_N1():
    N1 = request.json.get("N1", "").replace(" ", "").upper()
    valid = N1 in STATE["valid_N1"] and N1 not in STATE["used_N1"]
    log(f"validate_N1({N1[:4]}...) -> {'OK' if valid else 'FAIL'}")
    return jsonify({"valid": valid})


# ── tag N1 As used ──────────
@app.route("/api/consume_N1", methods=["POST"])
def consume_N1():
    N1 = request.json.get("N1", "").replace(" ", "").upper()
    if N1 not in STATE["valid_N1"] or N1 in STATE["used_N1"]:
        return jsonify({"ok": False, "error": "N1 invalide ou déjà consommé"})
    STATE["used_N1"].add(N1)
    for v in STATE["voters"].values():
        if v["N1"] == N1:
            v["voted"] = True
            break
    log(f"N1={N1[:4]}... consommé (vote enregistré)")
    return jsonify({"ok": True})


# ── Verification of hash(N2) ───────────────────────────
@app.route("/api/verify_tth_N2", methods=["POST"])
def verify_tth_N2():
    tth_n2 = request.json.get("tth_N2", "")
    valid = tth_n2 in STATE["tth_N2_set"]
    return jsonify({"valid": valid})


# ── state  ───────────────────────────────────────────────────────────────
@app.route("/api/state")
def get_state():
    return jsonify({
        "phase": STATE["phase"],
        "election_title": STATE["election_title"],
        "candidates": STATE["candidates"],
        "voter_count": len(STATE["voters"]),
        "voted_count": sum(1 for v in STATE["voters"].values() if v["voted"]),
        "audit": STATE["audit"][-30:],
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    STATE.update({
        "phase": "setup", "election_title": "", "candidates": [],
        "voters": {}, "valid_N1": set(), "used_N1": set(), "tth_N2_set": set(), "audit": [],
    })
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)