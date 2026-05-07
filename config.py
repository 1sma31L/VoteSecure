

COMMISSIONER_HOST  = "192.168.1.101"   # PC 1 — Commissonair
ADMINISTRATOR_HOST = "192.168.1.102"   # PC 2 — Administrator
ANONYMISER_HOST    = "192.168.1.103"   # PC 3 — Anonymisor
COUNTER_HOST       = "192.168.1.104"   # PC 4 — Décomptor
WEBSITE_HOST       = "192.168.1.100"   # PC 5 — web

# ─── Ports ─────────────────────────────────────
COMMISSIONER_PORT  = 5001
ADMINISTRATOR_PORT = 5002
ANONYMISER_PORT    = 5003
COUNTER_PORT       = 5004
WEBSITE_PORT       = 5000

# ─── URLs complètes ────────────────────────────────────────────────────────────
COMMISSIONER_URL  = f"http://{COMMISSIONER_HOST}:{COMMISSIONER_PORT}"
ADMINISTRATOR_URL = f"http://{ADMINISTRATOR_HOST}:{ADMINISTRATOR_PORT}"
ANONYMISER_URL    = f"http://{ANONYMISER_HOST}:{ANONYMISER_PORT}"
COUNTER_URL       = f"http://{COUNTER_HOST}:{COUNTER_PORT}"
WEBSITE_URL       = f"http://{WEBSITE_HOST}:{WEBSITE_PORT}"

# ─── Variables d'environnement à exporter ─────────────────────────────────────
# Collez ces exports dans votre terminal avant de lancer chaque service.

EXPORT_WEBSITE = f"""
# ─── PC 5 : Site Web ──────────────────
export COMMISSIONER_URL={COMMISSIONER_URL}
export ADMINISTRATOR_URL={ADMINISTRATOR_URL}
export ANONYMISER_URL={ANONYMISER_URL}
export COUNTER_URL={COUNTER_URL}
cd /chemin/vers/evote
python -m website.app
"""

EXPORT_ADMINISTRATOR = f"""
# ─── PC 2 : Administrateur ────────────
export COMMISSIONER_URL={COMMISSIONER_URL}
cd /chemin/vers/evote
python -m administrator.app
"""

EXPORT_ANONYMISER = f"""
# ─── PC 3 : Anonymiseur ───────────────
export COMMISSIONER_URL={COMMISSIONER_URL}
export ADMINISTRATOR_URL={ADMINISTRATOR_URL}
export COUNTER_URL={COUNTER_URL}
cd /chemin/vers/evote
python -m anonymiser.app
"""

EXPORT_COUNTER = f"""
# ─── PC 4 : Décompteur ────────────────
export COMMISSIONER_URL={COMMISSIONER_URL}
export ADMINISTRATOR_URL={ADMINISTRATOR_URL}
cd /chemin/vers/evote
python -m counter.app
"""

EXPORT_COMMISSIONER = f"""
# ─── PC 1 : Commissaire ───────────────
# (pas de dépendances vers les autres)
cd /chemin/vers/evote
python -m commissioner.app
"""

if __name__ == "__main__":
    print("configuration: ")
    print("="*60)
    print(f"  Commissionair → {COMMISSIONER_URL}")
    print(f"  Administrator → {ADMINISTRATOR_URL}")
    print(f"  Anonymisor → {ANONYMISER_URL}")
    print(f"  conter   → {COUNTER_URL}")
    print(f"  web    → {WEBSITE_URL}")
    print("="*60)
    print("\nCommandes à lancer sur chaque PC :")
    print(EXPORT_COMMISSIONER)
    print(EXPORT_ADMINISTRATOR)
    print(EXPORT_ANONYMISER)
    print(EXPORT_COUNTER)
    print(EXPORT_WEBSITE)
