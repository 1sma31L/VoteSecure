"""
commissioner/app.py — Service Commissaire
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
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["*"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

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
    """Send N1 and N2 codes to the voter by email (plain, no images)."""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Vos codes de vote — {title}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = to_email

    # Plain-text version
    text_body = f"""Hello {voter_name},

You are registered for the election: {title}

Your voting credentials:

N1 (Identification): {n1_fmt}
N2 (Anonymity):      {n2_fmt}

IMPORTANT:
- Do not share these codes with anyone.
- N1 is required to access the voting system.
- N2 ensures the anonymity of your ballot.

Secure. Transparent. Trustworthy."""

    # Simple HTML version — no images, no nested tables, minimal styling
    html_body = f"""
    <div style="font-family:Arial,Helvetica,sans-serif; color:#1e293b; max-width:560px; margin:0 auto; padding:32px 20px;">

      <p style="font-size:18px; margin:0 0 24px 0;">
        Hello <strong>{voter_name}</strong>,
      </p>

      <p style="font-size:15px; margin:0 0 8px 0; color:#475569;">
        You are registered for the election:
      </p>
      <p style="font-size:22px; font-weight:bold; margin:0 0 28px 0; color:#0f172a;">
        {title}
      </p>

      <p style="font-size:15px; margin:0 0 16px 0; color:#475569;">
        Your personal and confidential voting credentials:
      </p>

      <div style="margin-bottom:20px;">
        <div style="font-size:13px; font-weight:bold; color:#1d4ed8; margin-bottom:6px;">N1 — Identification</div>
        <div style="font-size:24px; font-weight:bold; letter-spacing:2px; color:#1e3a8a; font-family:monospace;">
          {n1_fmt}
        </div>
      </div>

      <div style="margin-bottom:28px;">
        <div style="font-size:13px; font-weight:bold; color:#15803d; margin-bottom:6px;">N2 — Anonymity</div>
        <div style="font-size:24px; font-weight:bold; letter-spacing:2px; color:#14532d; font-family:monospace;">
          {n2_fmt}
        </div>
      </div>

      <hr style="border:none; border-top:1px solid #e2e8f0; margin:28px 0;" />

      <p style="font-size:13px; font-weight:bold; color:#1d4ed8; margin:0 0 8px 0;">Important</p>
      <ul style="font-size:14px; color:#475569; line-height:1.7; margin:0; padding-left:20px;">
        <li>Do not share these codes with anyone.</li>
        <li>N1 is required to access the voting system.</li>
        <li>N2 ensures the anonymity of your ballot.</li>
      </ul>

      <hr style="border:none; border-top:1px solid #e2e8f0; margin:28px 0;" />
      <p style="font-size:12px; color:#94a3b8; margin:0; text-align:center;">
        Secure. Transparent. Trustworthy.
      </p>

    </div>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Send
    try:
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as ex:
        log(f"failed to send email to {to_email}: {ex}")
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
    log(f"N1 parsed = '{N1}'")
    log(f"VALID_N1 SET = {list(STATE['valid_N1'])}")
    valid = (
        N1 != ""
        and N1 in STATE["valid_N1"]
        and N1 not in STATE["used_N1"]
    )
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
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)